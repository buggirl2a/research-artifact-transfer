from __future__ import annotations
import gzip, io, struct
from pathlib import Path
from typing import Any, Iterable

PAR1=b'PAR1'
CT_STOP=0; CT_BOOL_TRUE=1; CT_BOOL_FALSE=2; CT_BYTE=3; CT_I16=4; CT_I32=5; CT_I64=6; CT_DOUBLE=7; CT_BINARY=8; CT_LIST=9; CT_SET=10; CT_MAP=11; CT_STRUCT=12
TYPE_INT64=2; TYPE_DOUBLE=5; TYPE_BYTE_ARRAY=6

def _uvar(f):
    n=0; shift=0
    while True:
        b=f.read(1)
        if not b: raise EOFError('truncated compact varint')
        x=b[0]; n|=(x&0x7f)<<shift
        if not (x&0x80): return n
        shift += 7
        if shift>70: raise ValueError('invalid varint')

def _unzig(n:int)->int: return (n>>1)^-(n&1)

class _CR:
    def __init__(self,f): self.f=f; self.last=[]
    def struct_begin(self): self.last.append(0)
    def struct_end(self): self.last.pop()
    def field(self):
        b=self.f.read(1)
        if not b: raise EOFError('truncated compact field')
        x=b[0]
        if x==0: return 0,0
        t=x&15; delta=x>>4
        fid=self.last[-1]+delta if delta else _unzig(_uvar(self.f))
        self.last[-1]=fid; return fid,t
    def integer(self): return _unzig(_uvar(self.f))
    def binary(self): return self.f.read(_uvar(self.f))
    def dbl(self): return struct.unpack('<d',self.f.read(8))[0]
    def list_header(self):
        x=self.f.read(1)[0]; n=x>>4; t=x&15
        if n==15: n=_uvar(self.f)
        return t,n
    def skip(self,t):
        if t in (CT_BOOL_TRUE,CT_BOOL_FALSE): return
        if t==CT_BYTE: self.f.read(1); return
        if t in (CT_I16,CT_I32,CT_I64): _uvar(self.f); return
        if t==CT_DOUBLE: self.f.read(8); return
        if t==CT_BINARY: self.binary(); return
        if t in (CT_LIST,CT_SET):
            et,n=self.list_header()
            for _ in range(n): self.skip(et)
            return
        if t==CT_MAP:
            n=_uvar(self.f)
            if n:
                x=self.f.read(1)[0]; kt=x>>4; vt=x&15
                for _ in range(n): self.skip(kt); self.skip(vt)
            return
        if t==CT_STRUCT:
            self.struct_begin()
            while True:
                _,tt=self.field()
                if tt==0: break
                self.skip(tt)
            self.struct_end(); return
        raise ValueError(f'unsupported compact type {t}')

def _schema_el(r):
    o={}; r.struct_begin()
    while True:
        fid,t=r.field()
        if t==0: break
        if fid in (1,3,5,6): o[fid]=r.integer()
        elif fid==4: o[fid]=r.binary().decode('utf-8')
        else: r.skip(t)
    r.struct_end(); return o

def _colmeta(r):
    o={}; r.struct_begin()
    while True:
        fid,t=r.field()
        if t==0: break
        if fid in (1,4,5,6,7,9): o[fid]=r.integer()
        elif fid==3:
            et,n=r.list_header(); o[3]=[r.binary().decode('utf-8') for _ in range(n)]
        else: r.skip(t)
    r.struct_end(); return o

def _colchunk(r):
    o={}; r.struct_begin()
    while True:
        fid,t=r.field()
        if t==0: break
        if fid==2: o['file_offset']=r.integer()
        elif fid==3: o['meta']=_colmeta(r)
        else: r.skip(t)
    r.struct_end(); return o

def _rowgroup(r):
    o={}; r.struct_begin()
    while True:
        fid,t=r.field()
        if t==0: break
        if fid==1:
            et,n=r.list_header(); o['columns']=[_colchunk(r) for _ in range(n)]
        elif fid in (2,3,6): o[fid]=r.integer()
        else: r.skip(t)
    r.struct_end(); return o

def parquet_metadata(path:str|Path)->dict[str,Any]:
    p=Path(path); size=p.stat().st_size
    with p.open('rb') as f:
        if f.read(4)!=PAR1: raise ValueError('Parquet missing PAR1 header')
        f.seek(-8,2); ml=struct.unpack('<I',f.read(4))[0]
        if f.read(4)!=PAR1: raise ValueError('Parquet missing PAR1 footer')
        if ml<=0 or ml>size-12: raise ValueError('invalid Parquet metadata length')
        f.seek(-8-ml,2); r=_CR(f); out={}; r.struct_begin()
        while True:
            fid,t=r.field()
            if t==0: break
            if fid in (1,3): out[fid]=r.integer()
            elif fid==2:
                et,n=r.list_header(); out['schema']=[_schema_el(r) for _ in range(n)]
            elif fid==4:
                et,n=r.list_header(); out['row_groups']=[_rowgroup(r) for _ in range(n)]
            elif fid==6: out['created_by']=r.binary().decode('utf-8')
            else: r.skip(t)
        r.struct_end()
    kinds={TYPE_BYTE_ARRAY:'string',TYPE_INT64:'int64',TYPE_DOUBLE:'double'}
    fields=[]
    for e in out['schema'][1:]:
        if e.get(1) not in kinds: raise ValueError(f'unsupported physical type: {e}')
        fields.append((e[4],kinds[e[1]]))
    return {'num_rows':out[3],'schema':fields,'row_groups':out['row_groups'],'created_by':out.get('created_by',''),'size_bytes':size}

def _page_header(f):
    r=_CR(f); out={}; r.struct_begin()
    while True:
        fid,t=r.field()
        if t==0: break
        if fid in (1,2,3): out[fid]=r.integer()
        elif fid==5: r.skip(t)
        else: r.skip(t)
    r.struct_end(); return out

def _plain(raw:bytes,kind:str,n:int):
    f=io.BytesIO(raw)
    if kind=='int64': return [struct.unpack('<q',f.read(8))[0] for _ in range(n)]
    if kind=='double': return [struct.unpack('<d',f.read(8))[0] for _ in range(n)]
    if kind=='string':
        out=[]
        for _ in range(n):
            b=f.read(4)
            if len(b)!=4: raise ValueError('truncated string length')
            ln=struct.unpack('<I',b)[0]; out.append(f.read(ln).decode('utf-8'))
        return out
    raise ValueError(kind)

def read_parquet_rows(path:str|Path,columns:list[str]|None=None,progress=None)->Iterable[dict[str,Any]]:
    md=parquet_metadata(path); schema=dict(md['schema'])
    cols=list(schema) if columns is None else list(columns)
    missing=[c for c in cols if c not in schema]
    if missing: raise KeyError(f'Parquet missing columns {missing}; available={list(schema)}')
    done=0
    with Path(path).open('rb') as f:
        for gi,rg in enumerate(md['row_groups'],1):
            n=int(rg[3]); cmap={c['meta'][3][0]:c for c in rg['columns']}; data={}
            for name in cols:
                c=cmap[name]; meta=c['meta']
                if int(meta[4])!=2: raise ValueError(f'unsupported codec for {name}: {meta[4]}')
                f.seek(int(meta[9])); ph=_page_header(f)
                comp=f.read(int(ph[3])); raw=gzip.decompress(comp)
                if len(raw)!=int(ph[2]): raise ValueError(f'uncompressed page length mismatch for {name}')
                data[name]=_plain(raw,schema[name],n)
            for i in range(n): yield {name:data[name][i] for name in cols}
            done += n
            if progress is not None: progress(done,int(md['num_rows']),gi,len(md['row_groups']))

def self_test(writer_cls,tmp:Path):
    schema=[('a','string'),('b','int64'),('c','double')]
    rows=[{'a':'x','b':1,'c':1.25},{'a':'y','b':2,'c':float('nan')},{'a':'z','b':3,'c':-2.5}]
    with writer_cls(tmp,schema,row_group_size=2) as w:
        for row in rows:w.write(row)
    md=parquet_metadata(tmp)
    got=list(read_parquet_rows(tmp))
    if md['num_rows']!=3 or [r['a'] for r in got]!=['x','y','z'] or got[0]['b']!=1 or abs(got[0]['c']-1.25)>1e-12:
        raise RuntimeError('mini parquet reader self-test failed')
    return md
