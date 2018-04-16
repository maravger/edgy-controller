#!/usr/bin/env python
# -*- coding:utf-8 -*-


import docker
import os
import sys


OperationIndex=[1,1,1,1,1,1]
RequestRatetoCreate=[15,12,10,8,7,9]
previousART=[3,4,4,5,5,2]

U_PES_MIN = [[0, 10, 20, 30, 40], [0, 10, 20, 30, 40]]
U_PES_MAX = [[0, 30, 40, 50, 60], [0, 30, 40, 50, 60]]
U_REQ_MIN = [[0, 0.5, 3.5, 4.5, 5.5], [0, 0.5, 3.5, 4.5, 5.5]]
U_REQ_MAX = [[0, 3.5, 5.5, 7.5, 10], [0, 3.5, 5.5, 7.5, 10]]
X_ART_REF = [[0, 2.5, 2.5, 2.5, 2.5], [0, 3.5, 3.5, 3.5, 3.5]]
U_PES_REF = [[0, 25, 35, 45, 55], [0, 25, 35, 45, 55]]
U_REQ_REF = [[0, 2.9522, 4.6272, 6.1769, 8.0228], [0, 3.2358, 5.2899, 7.375, 9.5755]]
K1 = [[0, 0, 0, 0, 0.84874], [0, 1.4286, 0, 0, 0.61825]]
K2 = [[0, -0.21913, -0.34912, -0.52926, -0.79089], [0, -0.075496, -0.060028, -0.035707, -0.1213]]
HOSTS = 3
HOST_PES = 100
MAX_TOTAL_VM_PES = (int)(0.9*HOST_PES)


def main():
    #print (OperationIndex)
    verticalScaler(OperationIndex,RequestRatetoCreate,previousART)


def verticalScaler(OperationIndex,RequestRatetoCreate,previousART):
    
    pesToScale = [2,4,5,6,4,5]    # plithos vms
    totalPesAlloc = [15,10,12]   #plithos hosts
    RRUprLim = [3,4,5,7,3,4]   # plhthos vms

#edw prepei oi listes na exoun ta swsta megethi
#####################################
    appIndex = 0 
    hostIndex = 0
    
    #print ('%' % ) 
    for vmIndex in range (0, len(pesToScale)): ##len(pesToScale)  == VmList.size()
     	print ('\nVM: %d \n OP: %d \n Host: %d \n' % (vmIndex, OperationIndex[vmIndex], hostIndex))
  
        x0 = previousART[vmIndex]
        print ('Previous ART: %f \n' % x0) 
        vmOpIdx = OperationIndex[vmIndex]
	#print (appIndex,vmOpIdx)    
        pesToScale[vmIndex]= (int) (K1[appIndex][vmOpIdx] )#* x0 - X_ART_REF[appIndex][vmOpIdx] + U_PES_REF[appIndex][vmOpIdx])
	
        if (pesToScale[vmIndex] > U_PES_MAX[appIndex][vmOpIdx]):
                pesToScale[vmIndex] = (int) (U_PES_MAX[appIndex][vmOpIdx])
        if (pesToScale[vmIndex] < U_PES_MIN[appIndex][vmOpIdx]):
       	        pesToScale[vmIndex] = (int) (U_PES_MIN[appIndex][vmOpIdx])
	
	print ("PES to allocate: %d \n" % pesToScale[vmIndex]) 
        
	totalPesAlloc[hostIndex] += pesToScale[vmIndex]
	print ("PES in Total: %d \n" % totalPesAlloc[hostIndex])

        RRUprLim[vmIndex] = (K2[appIndex][vmOpIdx] * (x0 - X_ART_REF[appIndex][vmOpIdx]) + U_REQ_REF[appIndex][vmOpIdx])

    	if (RRUprLim[vmIndex] > U_REQ_MAX[appIndex][vmOpIdx]):
                RRUprLim[vmIndex] = U_REQ_MAX[appIndex][vmOpIdx]
         
        if (RRUprLim[vmIndex] < U_REQ_MIN[appIndex][vmOpIdx]):
                RRUprLim[vmIndex] = U_REQ_MIN[appIndex][vmOpIdx]
        
	
	hostIndex+=1
        if (hostIndex == HOSTS):
        	hostIndex = 0
                appIndex+=1

	
    for hostIndex in range (0,HOSTS):
    	if (totalPesAlloc[hostIndex] > MAX_TOTAL_VM_PES):
		for vmIndex in range (0,len(pesToScale)):    ##len(pesToScale)  == VmList.size()
			pesToScale[vmIndex] = (int) (pesToScale[vmIndex] * MAX_TOTAL_VM_PES / totalPesAlloc[hostIndex])

    for  vmIndex in range (0, len(pesToScale)):  ##len(pesToScale)  == VmList.size()
	update ()	 

    
    appIndex = 0
    for vmIndex in range (0,len(pesToScale)):
	
	print ('VM: %d \n PreviousART: %f \n NextPes %d \n NextRequestRate %f \n' %(vmIndex, previousART[vmIndex],pesToScale[vmIndex],RRUprLim[vmIndex]))
	createWorkload()
	################# leipoun ta parakatw print ta opoia isws den xreiazontai
	#
	#   Log.printFormatted("\nCreated: " + clCreated[vmIdx][intervalsCounter] + "\n");
        #    if (((vmIdx+1) % HOSTS) == 0) appIdx++;
        #}
        #Log.printFormatted("Total Requests for App 1 in Interval: " + clCreatedPerApp[0][intervalsCounter] + "\n");
        #Log.printFormatted("Total Requests for App 2 in Interval: " + clCreatedPerApp[1][intervalsCounter] + "\n");







def update():
	print("update")


def createWorkload():
	print("kanoyme erga")






if __name__ == "__main__":
        main()
