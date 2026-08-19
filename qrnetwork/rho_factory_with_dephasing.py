import numpy as np
from functools import reduce
from primaryfn import Q 


link=int(input("enter the number of entangled links :"))
N=2*link #no. of qubits
I=Q.Pauli.I
X=Q.Pauli.X
Z=Q.Pauli.Z
zero=np.array([[1],[0]])  #|0>
one=np.array([[0],[1]])   #|1>

eta= Q.Bell.phi_plus
rho_0=np.outer(eta,eta.conj())
######################################################
rho_link=[rho_0 for i in range(link)]  #lint of the state of the each link
#DEPHASING NOISE
Lambda=float(input("enter the strength of dephasing parameter : "))   #Noise Parameter

t=[] #round in which the link is successfully generated
for i in range(link):
    o=int(input("enter the round in which the link no. "+str(i+1)+" is generated :"))
    t.append(o)

print("rounds in which links are generated :",t)
t_max=max(t)
#Waiting time for each link
w=[]
for i in range(link):
    l=t_max-t[i]
    w.append(l)
print("waiting time for each link :",w)
#Kraus Operators
K_0=(np.sqrt((1+Lambda)/2)) * I
K_1=(np.sqrt((1-Lambda)/2)) * Z
#print("K_0 :",K_0)
#print("K_1 :",K_1)
for i in range(link):
    for j in range(w[i]):
        rho_link[i]=np.kron(K_0,I) @ rho_link[i] @ np.kron(K_0,I).conj().T + np.kron(K_1,I) @ rho_link[i] @ np.kron(K_1,I).conj().T
    
#print("rho_link :",rho_link)
rho=reduce(np.kron,rho_link)
#Projectors
P_00=np.outer(zero,zero.conj())   #|0><0|
P_11=np.outer(one,one.conj())     #|1><1|
opr1=[I for i in range(N)]
opr1[1]=P_00
A=reduce(np.kron,opr1)
cnot=[]
for i in range(2,N,2):
    if i+1<N :
        opr2=[I for i in range(N)]
        opr2[1]=P_11
        opr2[i+1]=X
        cnot.append(A+reduce(np.kron,opr2))
        
#print(cnot)
for i in range(len(cnot)):
    rho=cnot[i] @ rho @ cnot[i].conj().T

#Measurement operators in loop
M_0=[]
M_1=[]
for i in range(2,N,2):
    if i+1<N:
        m1=[I for i in range(N)]
        m2=[I for i in range(N)]
        m1[i+1]=P_00
        m2[i+1]=P_11
        M_0.append(reduce(np.kron,m1))
        M_1.append(reduce(np.kron,m2))

prob=[]
for i in range(len(M_0)):
    p_0=np.trace(M_0[i] @ rho).item()
    p_1=np.trace(M_1[i] @ rho).item()
    p_0=np.real(p_0)
    p_1=np.real(p_1)
    p_n=p_0+p_1
    p_0=p_0/p_n
    p_1=p_1/p_n
    prob.append([p_0,p_1])

outcomes=["0","1"]
outcome=[]
for i in range(len(prob)):
    outcome.append(np.random.choice(outcomes, p=prob[i])) 
    if outcome[i] == "0":
        rho = M_0[i] @ rho @ M_0[i].conj().T / prob[i][0]
    elif outcome[i] == "1":
        rho = M_1[i] @ rho @ M_1[i].conj().T / prob[i][1]

#now form X gate (measurement followed gate)
X_gate=[]
for i in range(2,N,2):
    if i<N:
        x=[I for i in range(N)]
        x[i]=X
        X_gate.append(reduce(np.kron,x))

B=[]
for i in range(len(outcome)):
    B.append(int(outcome[i]))

#apply X-gate
for i in range(len(B)):
    if B[i]==1:
        rho=X_gate[i] @ rho @ X_gate[i].conj().T

#Apply Haddamard gate on 2nd qubit 
h=(1/np.sqrt(2))*np.array([[1,1],[1,-1]])
H=[I for i in range(N)]
H[1]=h
H=reduce(np.kron,H)
rho = H @ rho @ H.conj().T

#apply Z gate on qubit 1 (measurement followed gate)
z1=[I for i in range(N)]
z1[1]=P_00
z2=[I for i in range(N)]
z2[1]=P_11
z1=reduce(np.kron,z1)
z2=reduce(np.kron,z2)
p0_q2nd=np.trace(z1 @ rho).item()
p1_q2nd=np.trace(z2 @ rho).item()
#Probabilities for the outcomes of q   # Tr(rho * M)
prob_q2nd=[p0_q2nd,p1_q2nd]
outcomes_q2nd=["0","1"]
#normalize probability
prob_q2nd = np.real(prob_q2nd)
prob_q2nd = prob_q2nd / np.sum(prob_q2nd)
outcome_q2nd = np.random.choice(outcomes_q2nd, p=prob_q2nd)
print("Measurement outcome of q1 qubit :", outcome_q2nd)
t=[]
for j in range(2,N,2):
    if j+1<N :
      t.append(j+1)  
    
for i in range(len(B)):
    print("Measurement outcome of q"+str(t[i])+" qubit :",B[i])
#Measurement on q2nd
if outcome_q2nd == "0":
    rho = z1 @ rho @ z1.conj().T / p0_q2nd
elif outcome_q2nd == "1":
    rho = z2 @ rho @ z2.conj().T / p1_q2nd
#apply Z gate on 1st qubit (measurement followed gate)
z=[I for i in range(N)]
z[0]=Z
z=reduce(np.kron,z)
b_q2nd = int(outcome_q2nd)  # 2nd qubit measurement
if b_q2nd == 1:
    rho = z @ rho @ z.conj().T


###################################
print("\nFull Density Matrix before tracing (dim = 2^N):")
print(rho.shape)

# ==========================================
# PARTIAL TRACE (Replacing faulty projector loop)
# Tracing out measured qubits: index 1 and all odd indices (3, 5, 7, ...)
# Keeping unmeasured target qubits: index 0 and all even indices (2, 4, 6, ...)
# ==========================================

# Subsystem dimensions [2, 2, ..., 2] for N qubits
dims = [2] * N
trace_qubits = set([1] + t)  # Qubits to trace out: [1, 3, 5, ...]
keep_qubits = [k for k in range(N) if k not in trace_qubits]  # Qubits to keep: [0, 2, 4, ...]

# Reshape rho into a 2N-rank tensor
rho_tensor = rho.reshape(dims + dims)

# Build index lists for einsum
row_idx = list(range(N))
col_idx = list(range(N, 2 * N))
for q in trace_qubits:
    col_idx[q] = row_idx[q]  # Contract row and column indices for traced qubits

input_indices = row_idx + col_idx
output_indices = [row_idx[k] for k in keep_qubits] + [col_idx[k] for k in keep_qubits]

# Contract tensor along traced dimensions
rho_final_tensor = np.einsum(rho_tensor, input_indices, output_indices)

# Reshape to 2^link x 2^link square matrix
target_dim = 2 ** len(keep_qubits)
rho_final = rho_final_tensor.reshape((target_dim, target_dim))

print("\nFinal Target Density Matrix rho_final (Shape: " + str(rho_final.shape) + "):")
print(np.round(rho_final, 4))
