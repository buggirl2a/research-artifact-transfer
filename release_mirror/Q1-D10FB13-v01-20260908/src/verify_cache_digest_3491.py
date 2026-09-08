import hashlib
import sqlite3
import sys

if sqlite3.sqlite_version != "3.49.1":
    raise RuntimeError(f"SQLite 3.49.1 required, observed {sqlite3.sqlite_version}")

path = sys.argv[1]
con = sqlite3.connect("file:" + path + "?mode=ro", uri=True)
h = hashlib.sha256()
n = 0
for row in con.execute("SELECT PLT_CN,SPCD,printf('%.17g',y) FROM plot_species ORDER BY PLT_CN,SPCD"):
    h.update(("\t".join(str(x) for x in row) + "\n").encode("utf-8"))
    n += 1
con.close()
print(f"{sqlite3.sqlite_version}\t{h.hexdigest()}\t{n}")
