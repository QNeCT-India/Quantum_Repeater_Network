import numpy as np
from functools import reduce
from primaryfn import Q 

zero=np.array([[1],[0]])
one=np.array([[0],[1]])
I=Q.Pauli.I
X=Q.Pauli.X
Z=Q.Pauli.Z
Y=Q.Pauli.Y
CNOT=np.kron(np.outer(zero,zero.conj()),I)+np.kron(np.outer(one,one.conj()),X)
swap=(1/2)*(np.kron(I,I)+np.kron(Z,Z)+np.kron(Y,Y)+np.kron(X,X))
eta=Q.Bell.phi_plus
link=int(input("enter the no. of links :"))
N=2*link
rho_0=np.outer(eta,eta.conj())


###############################
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
#print("rho :",rho)
a=[]
for k in range(1,int(len(rho_link))):
    a.append(rho_link[k])

#print("a :",a)

###########################
P_00=np.outer(zero,zero.conj())
P_11=np.outer(one,one.conj())
rho=rho_link[0]
d=0
for i in range(N-1):
    dim=2*(i+2)-d
    if dim <= N-d :
        rho=np.kron(rho,a[i])
        #print("rho =", rho)
        #print("shape of rho :",rho.shape)
        b=[I for _ in range(dim-1)]
        b[-2]=swap
        P=reduce(np.kron,b)
        #print("P :",P)
        #print("shape of P :",P.shape)
        rho= P @ rho @ P.conj().T
        #print("rho :",rho)
        c=[I for _ in range(dim-1)]
        c[-1]=CNOT
        Cx=reduce(np.kron,c)
        rho=Cx @ rho @ Cx.conj().T
        #print("rho :",rho)
        m_0=[I for i in range(dim)]
        m_0[-1]=P_00
        M_0=reduce(np.kron,m_0)
        m_1=[I for _ in range(dim)]
        m_1[-1]=P_11
        M_1=reduce(np.kron,m_1)
        p_0=np.trace(M_0 @ rho).item()
        p_1=np.trace(M_1 @ rho).item()      
        #Probabilities for the outcomes of qubit   # Tr(rho * M)
        prob=[p_0,p_1]
        outcomes=["0","1"]
        #normalize probability
        prob = np.real(prob)
        prob = prob / np.sum(prob)
        outcome = np.random.choice(outcomes, p=prob)
        #print("Measurement outcome of qubit :", outcome)
        #Measurement on qubit
        if outcome == "0":
            rho = M_0 @ rho @ M_0.conj().T / p_0
        elif outcome == "1":
            rho = M_1 @ rho @ M_1.conj().T / p_1
        #apply X gate (measurement followed gate) 
        X_m=[I for i in range(dim)]                 
        X_m[-3]=X
        X_m=reduce(np.kron,X_m)
        b = int(outcome)  # qubit measurement
        if b == 1:
            rho = X_m @ rho @ X_m.conj().T
        #exclude the qubit that has been measured
        base=[zero,one]
        M=[I for i in range(dim)]
        M[-1]=base[b].conj().T
        M=reduce(np.kron,M)
        rho=M @ rho @ M.conj().T
        #print("rho :",rho)
        d=i+1
        e=dim-1
        

#apply Hadamard on 2nd qubit
h=(1/np.sqrt(2))*np.array([[1,1],[1,-1]])
H=[I for j in range(e)]
H[-1]=h
H=reduce(np.kron,H)
rho=H @ rho @ H.conj().T
#measurement on the 2nd qubit  
m1=[I for j in range(e)]
m1[-1]=P_00
M_0=reduce(np.kron,m1)
m2=[I for j in range(e)]
m2[-1]=P_11
M_1=reduce(np.kron,m2)
p_0=np.trace(M_0 @ rho).item()
p_1=np.trace(M_1 @ rho).item()
#Probabilities for the outcomes of 2nd qubit   # Tr(rho * M)
prob_q2=[p_0,p_1]
outcomes_q2=["0","1"]
#normalize probability
prob_q2 = np.real(prob_q2)
prob_q2 = prob_q2 / np.sum(prob_q2)
outcome_q2 = np.random.choice(outcomes_q2, p=prob_q2)
#print("Measurement outcome of q2 qubit :", outcome_q2)    
#Measurement on q2
if outcome_q2 == "0":
    rho = M_0 @ rho @ M_0.conj().T / p_0
elif outcome_q2 == "1":
    rho = M_1 @ rho @ M_1.conj().T / p_1

#apply Z gate on 1st qubit (measurement followed gate)
Z1_m=[I for j in range(e)]
Z1_m[0]=Z
Z1=reduce(np.kron,Z1_m)
b2 = int(outcome_q2)  # q2 measurement
if b2 == 1:
    rho = Z1 @ rho @ Z1.conj().T

#exclude the q2 qubit because we have measured it already
base=[zero,one]
M=[I for j in range(e)]
M[-1]=base[b2].conj().T
M=reduce(np.kron,M)
rho=M @ rho @ M.conj().T
print("rho :",rho) 




           
