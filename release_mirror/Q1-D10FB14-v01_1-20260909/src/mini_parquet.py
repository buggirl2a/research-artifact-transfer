from __future__ import annotations
import gzip, math, os, struct
from pathlib import Path
from typing import Iterable, Sequence, Any

# Minimal deterministic Parquet v1 writer for flat REQUIRED primitive columns.
# Supported logical kinds: string (BYTE_ARRAY UTF8), int64, double.
# Data pages use PLAIN encoding + deterministic GZIP compression (mtime=0).
# Missing-value convention for this REQUIRED-column writer: string='', int64=-1, double=NaN.
# This avoids a runtime dependency on pyarrow/fastparquet while producing standard Parquet files.

PAR1=b'PAR1'
# Thrift compact protocol types
CT_STOP=0; CT_BOOL_TRUE=1; CT_BOOL_FALSE=2; CT_BYTE=3; CT_I16=4; CT_I32=5; CT_I64=6; CT_DOUBLE=7; CT_BINARY=8; CT_LIST=9; CT_SET=10; CT_MAP=11; CT_STRUCT=12
# Parquet enums
TYPE_INT64=2; TYPE_DOUBLE=5; TYPE_BYTE_ARRAY=6
REQUIRED=0
ENC_PLAIN=0; ENC_RLE=3
CODEC_GZIP=2
PAGE_DATA=0
CONVERTED_UTF8=0


def _uvarint(n:int)->bytes:
    out=bytearray(); n=int(n)
    while True:
        b=n & 0x7f; n >>= 7
        if n: out.append(b|0x80)
        else: out.append(b); return bytes(out)

def _zig(n:int)->int:
    return (n << 1) ^ (n >> 63)

class _CW:
    def __init__(self): self.b=bytearray(); self.last=[]
    def struct_begin(self): self.last.append(0)
    def struct_end(self): self.last.pop()
    def field(self,fid:int,ctype:int):
        prev=self.last[-1]; delta=fid-prev
        if 0 < delta <= 15: self.b.append((delta<<4)|ctype)
        else:
            self.b.append(ctype); self.b.extend(_uvarint(_zig(fid)))
        self.last[-1]=fid
    def stop(self): self.b.append(0)
    def i32(self,n:int): self.b.extend(_uvarint(_zig(int(n))))
    def i64(self,n:int): self.b.extend(_uvarint(_zig(int(n))))
    def binary(self,x:bytes): self.b.extend(_uvarint(len(x))); self.b.extend(x)
    def string(self,s:str): self.binary(s.encode('utf-8'))
    def dbl(self,x:float): self.b.extend(struct.pack('<d',float(x)))
    def list_header(self,etype:int,n:int):
        if n <= 14: self.b.append((n<<4)|etype)
        else: self.b.append(0xF0|etype); self.b.extend(_uvarint(n))


def _schema_element(name:str, kind:str|None=None, num_children:int|None=None)->bytes:
    w=_CW(); w.struct_begin()
    if kind is not None:
        w.field(1,CT_I32); w.i32({'int64':TYPE_INT64,'double':TYPE_DOUBLE,'string':TYPE_BYTE_ARRAY}[kind])
        w.field(3,CT_I32); w.i32(REQUIRED)
    w.field(4,CT_BINARY); w.string(name)
    if num_children is not None:
        w.field(5,CT_I32); w.i32(num_children)
    if kind=='string':
        w.field(6,CT_I32); w.i32(CONVERTED_UTF8)
    w.stop(); w.struct_end(); return bytes(w.b)


def _data_page_header(num_values:int)->bytes:
    # PageHeader {type, uncompressed_page_size, compressed_page_size, data_page_header{...}}
    raise RuntimeError('internal: use _page_header')

def _page_header(num_values:int, uncompressed:int, compressed:int)->bytes:
    w=_CW(); w.struct_begin()
    w.field(1,CT_I32); w.i32(PAGE_DATA)
    w.field(2,CT_I32); w.i32(uncompressed)
    w.field(3,CT_I32); w.i32(compressed)
    w.field(5,CT_STRUCT); w.struct_begin()
    w.field(1,CT_I32); w.i32(num_values)
    w.field(2,CT_I32); w.i32(ENC_PLAIN)
    w.field(3,CT_I32); w.i32(ENC_RLE)
    w.field(4,CT_I32); w.i32(ENC_RLE)
    w.stop(); w.struct_end()
    w.stop(); w.struct_end(); return bytes(w.b)


def _column_metadata(kind:str, name:str, num_values:int, total_uncompressed:int, total_compressed:int, data_offset:int)->bytes:
    w=_CW(); w.struct_begin()
    w.field(1,CT_I32); w.i32({'int64':TYPE_INT64,'double':TYPE_DOUBLE,'string':TYPE_BYTE_ARRAY}[kind])
    w.field(2,CT_LIST); w.list_header(CT_I32,2); w.i32(ENC_PLAIN); w.i32(ENC_RLE)
    w.field(3,CT_LIST); w.list_header(CT_BINARY,1); w.string(name)
    w.field(4,CT_I32); w.i32(CODEC_GZIP)
    w.field(5,CT_I64); w.i64(num_values)
    w.field(6,CT_I64); w.i64(total_uncompressed)
    w.field(7,CT_I64); w.i64(total_compressed)
    w.field(9,CT_I64); w.i64(data_offset)
    w.stop(); w.struct_end(); return bytes(w.b)


def _column_chunk(file_offset:int, meta:bytes)->bytes:
    w=_CW(); w.struct_begin()
    w.field(2,CT_I64); w.i64(file_offset)
    w.field(3,CT_STRUCT); w.b.extend(meta)
    w.stop(); w.struct_end(); return bytes(w.b)


def _row_group(chunks:list[bytes], total_uncompressed:int, num_rows:int, total_compressed:int)->bytes:
    w=_CW(); w.struct_begin()
    w.field(1,CT_LIST); w.list_header(CT_STRUCT,len(chunks));
    for ch in chunks: w.b.extend(ch)
    w.field(2,CT_I64); w.i64(total_uncompressed)
    w.field(3,CT_I64); w.i64(num_rows)
    w.field(6,CT_I64); w.i64(total_compressed)
    w.stop(); w.struct_end(); return bytes(w.b)


def _file_metadata(schema:Sequence[tuple[str,str]], num_rows:int, row_groups:list[bytes])->bytes:
    w=_CW(); w.struct_begin()
    w.field(1,CT_I32); w.i32(1)
    w.field(2,CT_LIST); w.list_header(CT_STRUCT,len(schema)+1)
    w.b.extend(_schema_element('schema',None,len(schema)))
    for name,kind in schema: w.b.extend(_schema_element(name,kind,None))
    w.field(3,CT_I64); w.i64(num_rows)
    w.field(4,CT_LIST); w.list_header(CT_STRUCT,len(row_groups));
    for rg in row_groups: w.b.extend(rg)
    w.field(6,CT_BINARY); w.string('Q1 B12 mini_parquet deterministic writer v1')
    w.stop(); w.struct_end(); return bytes(w.b)


def _plain(values:list[Any], kind:str)->bytes:
    out=bytearray()
    if kind=='int64':
        for v in values:
            try: x=int(v)
            except Exception: x=-1
            out.extend(struct.pack('<q',x))
    elif kind=='double':
        for v in values:
            try: x=float(v)
            except Exception: x=float('nan')
            out.extend(struct.pack('<d',x))
    elif kind=='string':
        for v in values:
            if v is None: s=''
            elif isinstance(v,(dict,list,tuple)): 
                import json; s=json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            else: s=str(v)
            b=s.encode('utf-8'); out.extend(struct.pack('<I',len(b))); out.extend(b)
    else: raise ValueError(kind)
    return bytes(out)

class ParquetWriter:
    def __init__(self,path:str|Path,schema:Sequence[tuple[str,str]],row_group_size:int=50000,compresslevel:int=6):
        self.path=Path(path); self.schema=list(schema); self.row_group_size=int(row_group_size); self.compresslevel=int(compresslevel)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.f=self.path.open('wb'); self.f.write(PAR1); self.groups=[]; self.nrows=0; self.buf=[]
    def write(self,row:dict[str,Any]):
        self.buf.append(row)
        if len(self.buf)>=self.row_group_size: self.flush()
    def write_many(self,rows:Iterable[dict[str,Any]]):
        for r in rows: self.write(r)
    def flush(self):
        if not self.buf: return
        n=len(self.buf); chunks=[]; rg_u=0; rg_c=0
        for name,kind in self.schema:
            raw=_plain([r.get(name) for r in self.buf],kind)
            comp=gzip.compress(raw,compresslevel=self.compresslevel,mtime=0)
            hdr=_page_header(n,len(raw),len(comp)); off=self.f.tell()
            self.f.write(hdr); self.f.write(comp)
            tu=len(hdr)+len(raw); tc=len(hdr)+len(comp)
            meta=_column_metadata(kind,name,n,tu,tc,off)
            chunks.append(_column_chunk(off,meta)); rg_u+=tu; rg_c+=tc
        self.groups.append(_row_group(chunks,rg_u,n,rg_c)); self.nrows+=n; self.buf=[]
    def close(self):
        if self.f.closed: return
        self.flush(); meta=_file_metadata(self.schema,self.nrows,self.groups); self.f.write(meta); self.f.write(struct.pack('<I',len(meta))); self.f.write(PAR1); self.f.flush(); os.fsync(self.f.fileno()); self.f.close()
    def __enter__(self): return self
    def __exit__(self,*exc): self.close()

def write_parquet(path:str|Path, rows:Iterable[dict[str,Any]], schema:Sequence[tuple[str,str]], row_group_size:int=50000):
    with ParquetWriter(path,schema,row_group_size=row_group_size) as w: w.write_many(rows)


def footer_info(path:str|Path)->dict[str,int|str]:
    p=Path(path); size=p.stat().st_size
    with p.open('rb') as f:
        if f.read(4)!=PAR1: raise ValueError('missing PAR1 header')
        f.seek(-8,2); ml=struct.unpack('<I',f.read(4))[0]; magic=f.read(4)
        if magic!=PAR1: raise ValueError('missing PAR1 footer')
        if ml<=0 or ml>size-12: raise ValueError('invalid metadata length')
    return {'size_bytes':size,'metadata_length':ml,'magic':'PAR1'}
