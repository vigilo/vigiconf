## defaultBFNISG_primary
#	addCollectorServiceAndMetroAndGraph(o,'CpuAvg','.1.3.6.1.4.1.3224.16.1.1.0',50,80,1,'GAUGE','lines','Charge',metroFunction="percentage",graphGroupName="Perf")
## defaultBFNISG_secondary
#	addCollectorServiceAndMetroAndGraph(o,"CpuAvg",".1.3.6.1.4.1.3224.16.1.1.0",50,80,1,'GAUGE',"lines","Charge",metroFunction="percentage",graphGroupName="Perf")
## defaultRDH2Host
#	addCollectorMetro(o,"FreeMemory","directValue",[],['GET/.1.3.6.1.4.1.9.2.1.8.0'],'GAUGE')
#	addGraph(o,"Memoire libre",["FreeMemory"],'lines','octets', graphGroupName="Perf")
#	addCollectorMetro(o,'CPU Avg 1 min',"directValue",[],['GET/.1.3.6.1.4.1.9.2.1.57.0'],'GAUGE')
#	addCollectorMetro(o,'CPU Avg 5 min',"directValue",[],['GET/.1.3.6.1.4.1.9.2.1.58.0'],'GAUGE')
#	addGraph(o,"Charge CPU",["CPU Avg 1 min","CPU Avg 5 min"],'lines','%',graphGroupName="Perf")
#	addCollectorMetro(o,'bufferELMiss',"directValue",[],['GET/.1.3.6.1.4.1.9.2.1.12.0'],'GAUGE')
#	addCollectorMetro(o,'bufferMdMiss',"directValue",[],['GET/.1.3.6.1.4.1.9.2.1.27.0'],'GAUGE')
#	addCollectorMetro(o,'bufferHdMiss',"directValue",[],['GET/.1.3.6.1.4.1.9.2.1.67.0'],'GAUGE')
#	addGraph(o,"Buffers",["bufferELMiss","bufferMdMiss","bufferHdMiss"],'lines','nb occurences',graphGroupName="Perf")
## preInstOBSAgence
#    addCollectorService(o,"Serial Number", "directValue", [], ['GET/.1.3.6.1.4.1.9.3.6.3.0'],cti=0)
## preInst9CAgence
#    addCollectorService(o,"Serial Number", "directValue", [], ['GET/.1.3.6.1.2.1.47.1.1.1.1.11.1'],cti=0)
## defaultBFNISG_primary
#	addStdCollectorServiceAndMetro(o,'CpuAvg','.1.3.6.1.4.1.3224.16.1.1.0',50,80,1,'GAUGE',metroFunction="percentage",cti=25)
#	addStdCollectorServiceAndMetro(o,'CpuLast1min','.1.3.6.1.4.1.3224.16.1.2.0',50,80,1,'GAUGE',metroFunction="percentage",cti=25)
#	addStdCollectorServiceAndMetro(o,'CpuLast5min','.1.3.6.1.4.1.3224.16.1.3.0',50,80,1,'GAUGE',metroFunction="percentage",cti=25)
#	addStdCollectorServiceAndMetro(o,'CpuLast15min','.1.3.6.1.4.1.3224.16.1.4.0',50,80,1,'GAUGE',metroFunction="percentage",cti=25)
#	addGraph(o,"Charges CPU", [ "CpuAvg", "CpuLast1min", "CpuLast5min", "CpuLast15min"], 'lines', '%CPU',graphGroupName="Perf")
#	addStdCollectorServiceAndMetro(o,'nsResMemAllocate','.1.3.6.1.4.1.3224.16.2.1.0',1600000000,1750000000,1,'GAUGE',metroFunction="directValue",cti=25)
#	addStdCollectorServiceAndMetro(o,'nsResMemLeft','.1.3.6.1.4.1.3224.16.2.2.0',256000000,124000000,0,'GAUGE',metroFunction="directValue",cti=25)
#	addGraph(o,"Memory Usage", ["nsResMemAllocate", "nsResMemLeft"], 'area-line', 'bytes',graphGroupName="Perf")
#	addCollectorServiceAndMetroAndGraph(o,'nsResMemFrag','.1.3.6.1.4.1.3224.16.2.3.0',1000,2000,1,'GAUGE','lines','Octets',metroFunction="directValue",graphGroupName="Perf",cti=25)
#
## defaultBFNRT
#	jnxOperating(o,"PowerSupply0_Temp","Power Supply 0 temp sensor",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"PowerSupply1_Temp","Power Supply 1 temp sensor",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"MidPlane_Temp","midplane",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"CFEB_InTake_Temp","CFEB Intake temperature sensor",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"CFEB_Exhaust_Temp","CFEB Exhaust temperature sensor",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"FPC_Temp","FPC:  \@ 0\/\*\/\* temp sensor",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"Routing_Engine_Temp","Routing Engine",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"CFEB_CPU","CFEB Internet Processor II",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.8','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],70,80)
#	jnxOperating(o,"FPC_CPU","FPC:  @ 0\/\*\/\*",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.8','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],70,80)
#	jnxOperating(o,"Routing_Engine_CPU","Routing Engine",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.8','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],80,90)
#	jnxOperating(o,"CFEB_Memory","CFEB Internet Processor II",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.11','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"FPC_Memory","FPC:  @ 0\/\*\/\*",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.11','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],50,80)
#	jnxOperating(o,"Routing_Engine_Memory","Routing Engine",['WALK/.1.3.6.1.4.1.2636.3.1.13.1.11','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'],80,90)
#	jnxOpFan(o,"Fan_1", 'Fan 1', ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.6','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5'])
#	jnxOpFan(o,"Fan_2", 'Fan 2', ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.6','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5'])
#	jnxOpFan(o,"Fan_3", 'Fan 3', ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.6','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5'])
#	jnxOpFan(o,"Fan_4", 'Fan 4', ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.6','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5'])
##Metrologie routeur
##surveillance temperature alimentation 1
#	addCollectorMetro(o,"PS0temp", "m_jnx", ["Power ? Supply 0 temp sensor"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "PowerSupply0temperature", ["PS0temp"],'lines','C', graphGroupName="Perf")
##surveillance temperature alimentation 2
#	addCollectorMetro(o,"PS1temp", "m_jnx", ["Power Supply 1 temp sensor"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "PowerSupply1temperature", ["PS1temp"],'lines','C', graphGroupName="Perf")
##surveillance temperature Carte mere
#	addCollectorMetro(o,"midplanetemp", "m_jnx", ["midplane"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "midplanetemp", ["midplanetemp"],'lines','C', graphGroupName="Perf")
##surveillance temperature CFEB Intake
#	addCollectorMetro(o,"CFEBinTemp", "m_jnx", ["CFEB Intake temperature sensor"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "CFEB_Intake_Temp",["CFEBinTemp"],'lines','C', graphGroupName="Perf")
##surveillance temperature CFEB Exhaust
#	addCollectorMetro(o,"CFEBExTemp", "m_jnx", ["CFEB Exhaust temperature sensor"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "CFEB_Exhaust_Temp",["CFEBExTemp"],'lines','C', graphGroupName="Perf")
##surveillance FPC Temperature
#	addCollectorMetro(o,"FPCTemp", "m_jnx", ["FPC:  \@ 0\/\*\/\* temp sensor"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "FPC_Temp",["FPCTemp"],'lines','C', graphGroupName="Perf")
##surveillance Routing engine temp
#	addCollectorMetro(o,"RTETemp", "m_jnx", ["Routing Engine"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.7','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "RT_engine_temp",["RTETemp"],'lines','C', graphGroupName="Perf")
##surveillance charge CPU CFEB	
#	addCollectorMetro(o,"CFEBcpu", "m_jnx", ["CFEB Internet Processor II"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.8','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "CFEB_CPU",["CFEBcpu"],'lines','%', graphGroupName="Perf")
##surveillance charge FPC Cpu
#	addCollectorMetro(o,"FPCcpu", "m_jnx", ["FPC:  \@ 0\/\*\/\*"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.8','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "FPC_cpu",["FPCcpu"],'lines','%', graphGroupName="Perf")
##surveillance Routine engine CPU
#	addCollectorMetro(o,"RTEcpu", "m_jnx", ["Routing Engine"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.8','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "RT_engine_CPU",["RTEcpu"],'lines','%', graphGroupName="Perf")
##surveillance CFEB Memory
#	addCollectorMetro(o,"CFEBmem", "m_jnx", ["CFEB Internet Processor II"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.11','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "CFEB_mem",["CFEBmem"],'lines','%', graphGroupName="Perf")
##surveillance FPC Memory
#	addCollectorMetro(o,"FPCmem", "m_jnx", ["FPC:  \@ 0\/\*\/\*"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.11','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "FPC_mem",["FPCmem"],'lines','%', graphGroupName="Perf")
##surveillance Routing Engine Memory
#	addCollectorMetro(o,"RTEmem", "m_jnx", ["Routing Engine"], ['WALK/.1.3.6.1.4.1.2636.3.1.13.1.11','WALK/.1.3.6.1.4.1.2636.3.1.13.1.5','WALK/.1.3.6.1.4.1.2636.3.1.13.1.6'], 'GAUGE')
#	addGraph(o, "RTE_mem",["RTEmem"],'lines','%', graphGroupName="Perf")
#def addInterface_ISG(o,label,name,addr=''):
#    genericAdd(o,'interfaces',"Interface %s"%label,{'name':name,'address':addr})
#    h={3:"ifInOctets",5:"ifOutOctets"}
#    for (k,v) in h.iteritems():
#        addCollectorMetro(o,"%s%s"%(v,label),"interface",[name],[ "WALK/.1.3.6.1.4.1.3224.9.3.1.%s"%k,"WALK/.1.3.6.1.4.1.3224.9.1.1.2" ],'COUNTER')
#    addCollectorService(o,"Interface %s"%label,"ifOperStatus_ISG_if",[name,"i"], [ "WALK/.1.3.6.1.4.1.3224.9.1.1.2", "WALK/.1.3.6.1.4.1.3224.9.1.1.5" ],cti=225);
#    for type in ["Octets"]:
#        addGraph(o, "%s %s"%(type, label), [ "ifIn%s%s"%(type,label), "ifOut%s%s"%(type,label) ], "area-line", "bps","Interfaces",factors={"ifIn%s%s"%(type,label):8,"ifOut%s%s"%(type,label):8})
#    #for type in ["Discards", "Errors"]:
#    #    addGraph(o, "%s %s"%(type, label), [ "ifIn%s%s"%(type,label), "ifOut%s%s"%(type,label) ], "area-line", "packets/s","Interfaces")
#
#def addTunnel(o,label,name,addr,invert):
#    genericAdd(o,'interfaces',"Interface %s"%label,{'name':name,'address':addr})
#    h={3:"ifInOctets",5:"ifOutOctets"}
#    for (k,v) in h.iteritems():
#     addCollectorMetro(o,"%s%s"%(v,label),"interface_ISG",[name],[ "WALK/.1.3.6.1.4.1.3224.9.3.1.%s"%k ],'COUNTER')
#    addCollectorService(o,"Interface %s"%label,"ifOperStatus_ISG",[name,invert], ["WALK/.1.3.6.1.4.1.3224.4.1.1.1.4","WALK/.1.3.6.1.4.1.3224.4.1.1.1.20" ],cti=225);
#    for type in ["Octets"]:
#        addGraph(o, "%s %s"%(type, label), [ "ifIn%s%s"%(type,label), "ifOut%s%s"%(type,label) ], "area-line", "bps","Tunnels",factors={"ifIn%s%s"%(type,label):8,"ifOut%s%s"%(type,label):8})
#
#def addISGSessions(o,th1_Failed,th2_Failed,th1_Allocate,th2_Allocate,lower):
#    addStdCollectorServiceAndMetro(o,"SessionsFailed",  ".1.3.6.1.4.1.3224.16.3.4.0",th1_Failed,th2_Failed,lower,'GAUGE',cti=25)
#    #addStdCollectorServiceAndMetro(o,"SessionsAllocate",".1.3.6.1.4.1.3224.16.3.2.0",th1_Allocate,th2_Allocate,lower,'GAUGE',"thresholds_OID_plus_max","average_ISG_Sessions")
#    addCollectorMetro(o,"SessionsAllocate","percentage2values",[ ],[ "GET/.1.3.6.1.4.1.3224.16.3.2.0", "GET/.1.3.6.1.4.1.3224.16.3.3.0" ],'GAUGE')
#    addCollectorService(o,"SessionsAllocate","thresholds_OID_plus_max",[th1_Allocate,th2_Allocate,lower],[ "GET/.1.3.6.1.4.1.3224.16.3.2.0", "GET/.1.3.6.1.4.1.3224.16.3.3.0" ],cti=25)
#    addGraph(o, 'Sessions Failed', [ 'SessionsFailed' ], 'lines', 'Sessions',"Perf")
#    addGraph(o, 'Sessions Allocate', [ 'SessionsAllocate' ], 'lines', 'Sessions',"Perf")
#
#def jnxOperating(o,label,name,oids,th1,th2):
#    addCollectorService(o,label,"jnx2Thresholds",[name,th1,th2],oids,cti=23)
#
#def jnxOpFan(o, label, name, oids): 
#    addCollectorService(o,label,"jnxFan",[name],oids,cti=223)
#



# vim:set expandtab tabstop=4 shiftwidth=4:
