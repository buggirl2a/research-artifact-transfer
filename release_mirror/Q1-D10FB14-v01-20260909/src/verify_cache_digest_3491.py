import hashlib, sqlite3, sys
p=sys.argv[1]
c=sqlite3.connect(f"file:{p}?mode=ro",uri=True)
h=hashlib.sha256(); n=0
for row in c.execute("SELECT PLT_CN,SPCD,printf('%.17g',y) FROM plot_species ORDER BY PLT_CN,SPCD"):
    h.update(("\t".join(str(x) for x in row)+"\n").encode()); n+=1
print(sqlite3.sqlite_version,h.hexdigest(),n,sep="\t")
