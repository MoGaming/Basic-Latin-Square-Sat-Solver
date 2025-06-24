import os
import subprocess
import sys
import time

if len(sys.argv) < 2:
    print("Usage: python3 generate.py <latin square order> [sat solver seed]")
    sys.exit(1)
elif int(sys.argv[1]) < 0:
    print("Error: <latin square order> must be a positive integer.")
    sys.exit(1)

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
input_path = os.path.join(script_dir, "input.cnf")
output_path = os.path.join(script_dir, "output.txt")
kissat_path = os.path.join(parent_dir, "kissat-rel-4.0.2", "build", "kissat") # update this to your sat solver's location 

start_time = time.time()
dimacs_elapsed = 0
kissat_elapsed = 0
verify_elapsed = 0

n = int(sys.argv[1]) # n > 0
if len(sys.argv) >= 3:
    seed = int(sys.argv[2]) # any integer 
else:
    seed = None
clauses = []
latinSquare = [] # latin square output

def checkValid(square):
    n = len(square)
    if any(len(row) != n for row in square): # all rows are length n
        return False
    for row in square: # each row contains all symbols 0 to n-1 exactly once
        if sorted(row) != list(range(n)):
            return False
    for col_idx in range(n): # each column contains all symbols 0 to n-1 exactly once
        col = [square[row_idx][col_idx] for row_idx in range(n)]
        if sorted(col) != list(range(n)):
            return False
    return True

def get1DIndex(r, c, s): # row, col, symbol, 0 <= r, s, c <= n - 1
    return r * n * n + c * n + s + 1 # 1 to n^3

def get3DIndex(v): 
    v = v - 1
    r  = v // (n * n)
    c  = (v % (n * n)) // n
    s  = v % n
    return r, c, s # 0 <= r, c, s <= n - 1

for i in range(n): # fix first row and/or column of both squares, this speeds up finding a solution like in the case of MOLS of order 9 where it went from 32 min to 25 min
    clauses.append(str(get1DIndex(0, i, i)))
    clauses.append(str(get1DIndex(i, 0, i)))

for x in range(n):
    for y in range(n):
        clause1 = ""
        clause2 = ""
        clause3 = ""
        for z in range(n):
            clause1 = clause1 + str(get1DIndex(x,y,z)) + " "
            clause2 = clause2 + str(get1DIndex(x,z,y)) + " "
            clause3 = clause3 + str(get1DIndex(z,x,y)) + " "
            for w in range(z + 1, n):
                clauses.append("-" + str(get1DIndex(x,y,z)) + " -" + str(get1DIndex(x,y,w)))
                clauses.append("-" + str(get1DIndex(x,z,y)) + " -" + str(get1DIndex(x,w,y)))
                clauses.append("-" + str(get1DIndex(z,x,y)) + " -" + str(get1DIndex(w,x,y)))
        clauses.append(clause1)
        clauses.append(clause2)
        clauses.append(clause3)

variableCount = get1DIndex(n - 1, n - 1, n - 1)
clauseCount = len(clauses)

with open(input_path, "w") as f:
    f.write(f"p cnf {variableCount} {clauseCount}\n")
    for clause in clauses:
        f.write(f"{clause} 0\n") # repeat write is faster than string concat

dimacs_elapsed = round((time.time() - start_time) * 100)/100
print("Wrote DIMACS CNF file to:", input_path)  # might move this is a c++ or c implementation to speed it up
    
verify_time = time.time()
with open(output_path, "w") as out_file:
    commands = [kissat_path, input_path]
    if seed != None: 
        commands.insert(1, "--seed=" + str(seed))
    subprocess.run(commands, stdout=out_file, stderr=subprocess.STDOUT)

print("Wrote Kissat output to:", output_path)

with open(output_path, "r") as f:
    satisfiable = None
    for x in range(n):
        latinSquare.append([])
        for y in range(n):
            latinSquare[x].append(-1) # easily tells us if logic error occured by the existance of -1 symbol
    for line in f:
        if line.startswith("s "):
            if "UNSATISFIABLE" in line:
                satisfiable = "UNSAT"
            elif "SATISFIABLE" in line:
                satisfiable = "SAT"
        elif line.startswith("v "):
            values = line[2:].strip().split()
            for val in values:
                if val == '0': # end of variables
                    continue
                val = int(val)
                if val > 0:
                    r, c, s = get3DIndex(val)
                    latinSquare[r][c] = s
        elif line.startswith("c process-time"):
            text = line.split()
            kissat_elapsed = text[len(text) - 2] # cpu time

    print("Result:", satisfiable)
    if satisfiable == "SAT":
        for row in latinSquare:
            print(row)
        if checkValid(latinSquare):
            print("\nValid solution produced by Kissat for a latin square of order", str(n) + ".")
        else:
            print("\nInvalid solution produced by Kissat")
verify_elapsed = round((time.time() - verify_time) * 100)/100
print("Total elapsed time of script:", round((time.time() - start_time) * 100)/100, "seconds")
print("     Dimacs elapsed time:", dimacs_elapsed, "seconds")
print("     Kissat elapsed time:", kissat_elapsed, "seconds")
print("     Verification elapsed time:", round((verify_elapsed - float(kissat_elapsed)) * 100)/100, "seconds")
# cd /mnt/g/Code/sat\ solver\ stuff/latin\ square
# python3 generate.py [order]
