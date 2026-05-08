#!/bin/bash

# Started by AICoder, pid:rab2fwc868n8c3e146ba09ed30b6b654f2d921e9 
get_proc_info_base()
{
        local pid=$1
        local prefix=$2
        local type=$3  # 0:普通 1:longtime 2:no_mstat_show

        # 执行 TASK_I 命令
        echo -e "\n===============================  $prefix TASK_I BEGIN  ================================\n"
        echo -e "\nTASK_I in $pid process"
        /ushell -NoBreak -pad $pid -t 5000 -c "i"
        echo -e "\n===============================  $prefix TASK_I END  ================================\n"

        # 执行 PCB 命令
        echo -e "\n===============================  $prefix PCB BEGIN  ================================\n"
        echo -e "\nPCB in $pid process"
        /ushell -NoBreak -pad $pid -t 5000 -c "PCB"
        echo -e "\n===============================  $prefix PCB END  ================================\n"

        # 执行 ShowProcCfg 命令
        echo -e "\n===============================  $prefix ShowProcCfg BEGIN  ================================\n"
        echo -e "\nShowProcCfg in $pid process"
        /ushell -NoBreak -pad $pid -t 5000 -c "ShowProcCfg"
        echo -e "\n===============================  $prefix ShowProcCfg END  ================================\n"

        # Started by AICoder, pid:daab7ae1c6zbb1114dcc09dd6071f20ac656b797
        # 执行 OSS_ShowBigUbUseInfo 命令
        /ushell -NoBreak -pad $pid -t 5000 -c "ConfigUshellFile \"OSS_ShowBigUbUseInfo\""
        echo -e "\n===============================  $prefix OSS_ShowBigUbUseInfo BEGIN  ================================\n"
        echo -e "\OSS_ShowBigUbUseInfo in $pid process"
        /ushell -NoBreak -pad $pid -t 5000 -c "OSS_ShowBigUbUseInfo"
        echo -e "\n===============================  $prefix OSS_ShowBigUbUseInfo END  ================================\n"
        # Ended by AICoder, pid:daab7ae1c6zbb1114dcc09dd6071f20ac656b797

        # 执行 Malloc_Size 命令
        echo -e "\n===============================  $prefix Malloc_Size BEGIN  ================================\n"
        echo -e "\nMalloc_Size in $pid process"
        /ushell -NoBreak -pad $pid -t 5000 -c "computeTotalMallocSize 0"
        echo -e "\n===============================  $prefix Malloc_Size END  ================================\n"

        # 根据类型执行不同的内存统计命令
        if [ "$type" = "2" ]; then
                /ushell -NoBreak -pad $pid -t 30000 -c "ConfigUshellFile \"ShowPools\""
                echo -e "\n===============================  $prefix OSS_Mem_Pools BEGIN  ================================\n"
                echo -e "\nOssMalloc in $pid process"
                /ushell -NoBreak -pad $pid -t 30000 -c "ShowPools 0,0"
                echo -e "\n===============================  $prefix OSS_Mem_Pools END  ================================\n"
        else
                # Started by AICoder, pid:wd634b339ev911a1458f092500424b1001c0991a 
                echo -e "\n===============================  $prefix OSS_Malloc BEGIN  ================================\n"
                echo -e "\nOssMalloc in $pid process"
                first_time=$(date +%s)
                /ushell -NoBreak -pad $pid -t 30000 -c "mstat_show 100, 100,0"
                second_time=$(date +%s)
                difference=$((second_time - first_time))
                echo "first_time: $(date --date @$first_time +'%Y-%m-%d %H:%M:%S')"
                echo "second_time: $(date --date @$second_time +'%Y-%m-%d %H:%M:%S')"
                echo "second_time-first_time: $difference s"
                echo -e "\n===============================  $prefix OSS_Malloc END  ================================\n"
                # Ended by AICoder, pid:wd634b339ev911a1458f092500424b1001c0991a
        fi
}

# 普通信息收集函数
get_proc_info()
{
        get_proc_info_base "$1" "$2" "0"
}

# 长时间信息收集函数
get_proc_info_longtime()
{
        echo -e "\ncap long time\n"
        get_proc_info_base "$1" "$2" "1"
}

# 不使用mstat_show的信息收集函数
get_proc_info_no_mstat_show()
{
        get_proc_info_base "$1" "$2" "2"
}
# Ended by AICoder, pid:rab2fwc868n8c3e146ba09ed30b6b654f2d921e9 

get_proc_proc()
{

        echo -e "\n=============================== $2 SMAPS BEGIN ================================\n"
        echo -e "\ncat /proc/$1/smaps"
        cat /proc/$1/smaps | grep -E '\-|^Size:|^Rss:|^AnonHugePages:|^Swap:' 
        echo -e "\n=============================== $2 SMAPS END ================================\n"
}

# Started by AICoder, pid:6fd9de841e3f02114e0809b6a0e7c65d49b5a483
get_container_mem()
{
        DOCKER_UID=`cat /proc/self/cgroup | sed -e "s/.*pids:\/docker\/\(.*\)/\\1/" | cut -c 1-12`
        echo -e "\n=============================== ${DOCKER_UID} PS BEGIN ================================\n"
        ps

        CONTAINER_PID=`ps | grep "$1" | grep -v "grep" | grep -v ".sh" |head -n 1|awk '{print $1}'`
        if [ -z "${CONTAINER_PID}" ];then
            CONTAINER_PID=`ps | grep ".exe" | grep -v "grep" | grep -v ".sh" |head -n 1|awk '{print $1}'`
            echo "$1 is not grep ,searching .exe"
            if [ -z "${CONTAINER_PID}" ];then
               echo "$1 is not start"
               echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"
               exit 1
            fi
        fi

        echo "Starting collect ${CONTAINER_PID}"
        echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"

        USHELL_PID=`ps | grep "ushell" | grep -v "grep" |awk '{print $1}'`
        if [ -n "${USHELL_PID}" ];then
           echo "kill ushell process ${USHELL_PID},pad ${CONTAINER_PID},ok"
           kill  ${USHELL_PID}
        else
           echo "pad ${CONTAINER_PID},no ushell run, ok"
        fi

        get_proc_proc ${CONTAINER_PID} ${DOCKER_UID}

        SWM_ID=`ps | grep "swm.exe" | grep -v "grep"|awk '{print $1}'`
        if [ -n "${SWM_ID}" ];then
           echo -e "\n=============================== VMP BEGIN ================================\n"
           echo -e "\nVMP in ${CONTAINER_PID} process"
           /ushell -NoBreak -pad ${CONTAINER_PID} -t 2000  -c "VMP"
           echo -e "\n=============================== VMP END ================================\n"
        fi

        # Started by AICoder, pid:e7b05g9d76k2f0e144ed08df10711515b0e96adb 
        BUM_ID=`ps | grep "bum" | grep -v "grep"|awk '{print $1}'`
        BES_ID=`ps | grep "bes" | grep -v "grep"|awk '{print $1}'`
        X2M_ID=`ps | grep "bes" | grep -v "grep"|awk '{print $1}'`
        LOG_ID=`ps | grep "log" | grep -v "grep"|awk '{print $1}'`
        HUC_ID=`ps | grep "huc" |  grep -v "hucm" | grep -v "grep"|awk '{print $1}'`
        HCCM_ID=`ps | grep "hccm" | grep -v "grep"|awk '{print $1}'`
        SWM_ID=`ps | grep "swm" | grep -v "grep"|awk '{print $1}'`
        NFC_ID=`ps | grep "nfcpmp" | grep -v "grep"|awk '{print $1}'`
        RUM_ID=`ps | grep "rum" | grep -v "grep"|awk '{print $1}'`
        LUC_ID=`ps | grep "luc" |  grep -v "lucm" | grep -v "grep"|awk '{print $1}'`
        XNM_ID=`ps | grep "xnm" | grep -v "grep"|awk '{print $1}'`
        if [[ -n "${BUM_ID}" ]]  ||  [[ -n "${BES_ID}" ]]  ||  [[ -n "${X2M_ID}" ]]  ||  [[ -n "${LOG_ID}" ]]  ||   [[ -n "${HCCM_ID}" ]]  || [[ -n "${RUM_ID}" ]]  || [[ -n "${NFC_ID}" ]]  || [[ -n "${SWM_ID}" ]];then
            get_proc_info_longtime ${CONTAINER_PID} ${DOCKER_UID}
        elif [[ -n "${HUC_ID}" ]]  ||  [[ -n "${LUC_ID}" ]] || [[ -n "${XNM_ID}" ]];then
            get_proc_info_no_mstat_show ${CONTAINER_PID} ${DOCKER_UID}
        else
            get_proc_info ${CONTAINER_PID} ${DOCKER_UID}
        fi
        # Ended by AICoder, pid:e7b05g9d76k2f0e144ed08df10711515b0e96adb 
}
# Ended by AICoder, pid:6fd9de841e3f02114e0809b6a0e7c65d49b5a483

get_ro_container_mem()
{
        DOCKER_UID=`cat /proc/self/cgroup | sed -e "s/.*pids:\/docker\/\(.*\)/\\1/" | cut -c 1-12`
        echo -e "\n=============================== ${DOCKER_UID} PS BEGIN ================================\n"
        ps

        RO_CONTAINER_PID=`ps |grep "/ro"| grep -v "sh" |grep -v "grep" | awk '{print $1}'`
        if [ -z "${RO_CONTAINER_PID}" ];then
            RO_CONTAINER_PID=`ps |grep "/ro"| grep -v "sh" |grep -v "grep" | awk '{print $1}'`
            echo "$1 is not grep ,searching .exe"
            if [ -z "${RO_CONTAINER_PID}" ];then
               echo "$1 is not start"
               echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"
               exit 1
            fi
        fi

        echo "Starting collect ${RO_CONTAINER_PID}"
        echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"

        USHELL_PID=`ps | grep "ushell" | grep -v "grep" |awk '{print $1}'`
        if [ -n "${USHELL_PID}" ];then
           echo "kill ushell process ${USHELL_PID},pad ${RO_CONTAINER_PID},ok"
           kill  ${USHELL_PID}
        else
           echo "pad ${RO_CONTAINER_PID},no ushell run, ok"
        fi


        get_proc_proc ${RO_CONTAINER_PID} ${DOCKER_UID}
        get_proc_info ${RO_CONTAINER_PID} ${DOCKER_UID}
}


get_sh_container_mem()
{
        DOCKER_UID=`cat /proc/self/cgroup | sed -e "s/.*pids:\/docker\/\(.*\)/\\1/" | cut -c 1-12`
        echo -e "\n=============================== ${DOCKER_UID} PS BEGIN ================================\n"
        ps

        SH_DOCKER_UID=`ps | grep "./sh" | grep -v "sh.sh" | grep -v "grep" | awk '{print $1}'`
        if [ -z "${SH_DOCKER_UID}" ];then
            SH_DOCKER_UID=`ps | grep "./sh" | grep -v "sh.sh" | grep -v "grep" | awk '{print $1}'`
            echo "$1 is not grep ,searching .exe"
            if [ -z "${SH_DOCKER_UID}" ];then
               echo "$1 is not start"
               echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"
               exit 1
            fi
        fi

        echo "Starting collect ${SH_DOCKER_UID}"
        echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"

        USHELL_PID=`ps | grep "ushell" | grep -v "grep" |awk '{print $1}'`
        if [ -n "${USHELL_PID}" ];then
           echo "kill ushell process ${USHELL_PID},pad ${SH_DOCKER_UID},ok"
           kill  ${USHELL_PID}
        else
           echo "pad ${SH_DOCKER_UID},no ushell run, ok"
        fi

        get_proc_proc ${SH_DOCKER_UID} ${DOCKER_UID}
        get_proc_info ${SH_DOCKER_UID} ${DOCKER_UID}
}

get_weblmt_container_mem()
{
        DOCKER_UID=`cat /proc/self/cgroup | sed -e "s/.*pids:\/docker\/\(.*\)/\\1/" | cut -c 1-12`
        echo -e "\n=============================== ${DOCKER_UID} PS BEGIN ================================\n"
        ps

        WEBLMT_DOCKER_UID=`ps |grep "/weblmt" | grep -v "sh" | grep -v "nginx" | grep -v "grep" | grep -v "tcpsvd" | head -n 1 | awk '{print $1}'`
        if [ -z "${WEBLMT_DOCKER_UID}" ];then
            WEBLMT_DOCKER_UID=`ps | grep "./sh" | grep -v "sh.sh" | grep -v "grep" | awk '{print $1}'`
            echo "$1 is not grep ,searching .exe"
            if [ -z "${WEBLMT_DOCKER_UID}" ];then
               echo "$1 is not start"
               echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"
               exit 1
            fi
        fi

        echo "Starting collect ${WEBLMT_DOCKER_UID}"
        echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"

        USHELL_PID=`ps | grep "ushell" | grep -v "grep" |awk '{print $1}'`
        if [ -n "${USHELL_PID}" ];then
           echo "kill ushell process ${USHELL_PID},pad ${WEBLMT_DOCKER_UID},ok"
           kill  ${USHELL_PID}
        else
           echo "pad ${WEBLMT_DOCKER_UID},no ushell run, ok"
        fi

        get_proc_proc ${WEBLMT_DOCKER_UID} ${DOCKER_UID}
        get_proc_info ${WEBLMT_DOCKER_UID} ${DOCKER_UID}
}

get_apmac_container_mem()
{
        DOCKER_UID=`cat /proc/self/cgroup | sed -e "s/.*pids:\/docker\/\(.*\)/\\1/" | cut -c 1-12`
        echo -e "\n=============================== ${DOCKER_UID} PS BEGIN ================================\n"
        ps

        APMC_DOCKER_UID=`ps |grep apmc |grep -v "_go"|grep -v ".sh"|grep -v "grep" | head -n 1 | awk '{print $1}'`
        if [ -z "${WEBLMT_DOCKER_UID}" ];then
            APMC_DOCKER_UID=`ps | grep "./sh" | grep -v "sh.sh" | grep -v "grep" | awk '{print $1}'`
            echo "$1 is not grep ,searching .exe"
            if [ -z "${APMC_DOCKER_UID}" ];then
               echo "$1 is not start"
               echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"
               exit 1
            fi
        fi

        echo "Starting collect ${APMC_DOCKER_UID}"
        echo -e "\n=============================== ${DOCKER_UID} PS END ================================\n"

        USHELL_PID=`ps | grep "ushell" | grep -v "grep" |awk '{print $1}'`
        if [ -n "${USHELL_PID}" ];then
           echo "kill ushell process ${USHELL_PID},pad ${APMC_DOCKER_UID},ok"
           kill  ${USHELL_PID}
        else
           echo "pad ${APMC_DOCKER_UID},no ushell run, ok"
        fi

        get_proc_proc ${APMC_DOCKER_UID} ${DOCKER_UID}
        get_proc_info ${APMC_DOCKER_UID} ${DOCKER_UID}
}

names_array="
sctp-ng=ngsctp.exe
sctp-xn=xnsctp.exe
bum=bum.exe
bsa=bsa.exe
rum=rum.exe
certm=certm.exe
nf-amp=nfamp.exe
log=log.exe
nfc-pmp=nfcpmp.exe
lcs=lcs.exe
cos=cos.exe
bes=bes
docs=docs
xnsc=xnsc
usm=usm.exe
dps-snr=dps.exe
dps=dps.exe
umftaskmanager=umf_task_manager.exe
swm=swm.exe
umfttd=umf_ttd.exe
pcs=pcs.exe
pcs=pcs_go
cocs=cocs
ro=ro
ces=ces
huc=huc
luc=luc
sh=sh
anr=anr
lrrm=lrrm_lf
pci=pci
ncm=ncm
lrrm-sub1g=lrrm_sub1g
uds-snr=uds-snr
uds=uds
nrdbs=vNrDbsServer.exe
cpf-dts=cpf_udt_dts.exe
hccm=hccm
udc=udc
lucm=lucm
ncs-modb=ms-modb
cms-modb=ms-modb
lccm=lccm
hrrm=hrrm
dson-modb=ms-modb
cf1m=cf1m
dpf-dts=dpf_udt_dts.exe
rct-agent=rct_agent.exe
bpf-dts=bpf_udt_dts.exe
cis-modb=ms-modb
bcs-modb=ms-modb
de1m=de1m
mim=mim
pces-modb=ms-modb
ucs-modb=ms-modb
ce1m=ce1m
xnm=xnm
son-modb=ms-modb
bf1m=bf1m
ngm=ngm
x2m=x2m
hucm=hucm
gis-modb=ms-modb
brs=brs.exe
gsm=gsm.exe
umts=UMTS_APP.EXE
nbiot=nbiot.exe
lte-union=lte_union.exe
idp=idpsmain.exe
idb=idb.exe
rse=rsemain.exe
apm=apmcenter.exe
webmnt=webmnt
weblmt=weblmt
dra=dra_adapt.exe
nf-ose=pse-engine
"

elf_name=""
get_elf_name()
{  
    container_name="$1"
    # arm单板容器，对应容器名称存在使用-arm结尾，但是进程名称不是-arm结尾，为了统一先处理掉容器名称中的-arm结尾
    if [[ "$container_name" == *-arm ]]; then
      container_name_base="${container_name%-arm}"
    else
      container_name_base="$container_name"
    fi

    elf_name=""      
    for item in ${names_array}
    do      
        key=${item%=*}     
        if [ "$key" = "$container_name_base" ]; then   
                value="${item#*=}"                                                              
                elf_name="$value"
                break;                     
        fi                                                             
    done                                                                                                                         
}
 


if [ "$1" == "env" ]; then
  echo "source env"
else
        SCRIPT=$0
        echo "$SCRIPT"
        cp -f "$SCRIPT" "/logs/oss/oss"; 
        ps

        PLAT_PID=`ps | grep "HWM.EXE" | grep -v "grep" |awk '{print $1}'`
        if [ -z "${PLAT_PID}" ];then
                echo "HWM.EXE is not start"
                exit 1
        fi  

        BOARD_USHELL_PID=`ps | grep "ushell" | grep -v "grep" |awk '{print $1}'`
        if [ -n "${BOARD_USHELL_PID}" ];then
                echo "kill ushell process ${BOARD_USHELL_PID},pad ${PLAT_PID},ok"
                kill  ${BOARD_USHELL_PID}
        else
                echo "pad ${PLAT_PID},no ushell run, ok"
        fi

        echo -e "\n******************************* MEM INFO BEGIN *******************************n"

        echo -e "\nuname"
        uname -a

        echo -e "\nifconfig"
        ifconfig

        echo -e "\ndate"
        date

        echo -e "\n=============================== UPTIME BEGIN ================================\n"
        echo -e "\nuptime"
        uptime
# Started by AICoder, pid:05a93x2616468f31429c0a37f0908c0404e21c60 
        echo -e "\nstart date"
        uptime -s
# Ended by AICoder, pid:05a93x2616468f31429c0a37f0908c0404e21c60
        echo -e "\n=============================== UPTIME END ================================\n"

        echo -e "\nfree"
        free

        echo -e "\necho 3 > /proc/sys/vm/drop_caches"
        echo 3 > /proc/sys/vm/drop_caches

        echo -e "\n=============================== FREE BEGIN ================================\n"
        echo -e "\nfree"
        free
        echo -e "\n=============================== FREE END ================================\n"

        echo -e "\n=============================== TOP BEGIN ================================\n"
        echo -e "\ntop"
        top -m -n 1 -b
        echo -e "\n=============================== TOP END ================================\n"

        echo -e "\n=============================== CPU TOP BEGIN ================================\n"
		    for i in {1..5};do
			    /ushell -NoBreak -pad ${PLAT_PID} -t 5 -c "OSS_GetCpuUseRate"
			    sleep 2
		    done
        echo -e "\n=============================== CPU TOP END ================================\n"

        echo -e "\n=============================== DOCKERPS BEGIN ================================\n"
        echo -e "\ndocker ps"
        docker ps
        echo -e "\n=============================== DOCKERPS END ================================\n"

        echo -e "\n=============================== DOCKERSTATS BEGIN ================================\n"
        echo -e "\ndocker stats"
        docker stats --no-stream
        echo -e "\n=============================== DOCKERSTATS END ================================\n"

        echo -e "\n=============================== MEMINFO BEGIN ================================\n"
        echo -e "\ncat /proc/meminfo"
        cat /proc/meminfo
        echo -e "\n=============================== MEMINFO END ================================\n"

        echo -e "\n=============================== BASEINFO BEGIN ================================\n"
        echo -e "\ncat /proc/mm/baseinfo"
        cat /proc/mm/baseinfo
        echo -e "\n=============================== BASEINFO END ================================\n"

        echo -e "\n=============================== SWAPINFO BEGIN ================================\n"
        echo -e "\ncat /sys/block/zram0/mm_stat"
        cat /sys/block/zram0/mm_stat
        echo -e "\n=============================== SWAPINFO END ================================\n"

        echo -e "\n=============================== KERNELINFO BEGIN ================================\n"
        echo -e "\ncat /proc/mm/kernelinfo"
        cat /proc/mm/kernelinfo
        echo -e "\n=============================== KERNELINFO END ================================\n"

        echo -e "\n=============================== VSWC_SMBUS BEGIN ================================\n"
        cat /logs/BSP/clockstatuslog.txt | grep "T= " | grep -v "R= " | tail -1
        echo -e "\n=============================== VSWC_SMBUS END ================================\n"

        echo -e "\n=============================== PROCESSINFO BEGIN ================================\n"
        echo -e "\ncat /proc/mm/processinfo"
        cat /proc/mm/processinfo
        echo -e "\n=============================== PROCESSINFO END ================================\n"

        echo -e "\n=============================== FILEINFO BEGIN ================================\n"
        echo -e "\ncat /proc/mm/fileinfo"
        cat /proc/mm/fileinfo
        echo -e "\n=============================== FILEINFO END ================================\n"
        
	
        echo -e "\n=============================== RAMDISK BEGIN ================================\n"
        echo -e "\ndf"
        df
        echo -e "\nls -l"
        ls -l /

        # Started by AICoder, pid:nee502fe9ef46621421e0a17d05def099a62e77f 
        echo -e "\ndu / -d 1 --exclude=/proc"
        find / -mindepth 1 -maxdepth 1 -type d ! -name "proc" -exec du -sh {} +
        # Ended by AICoder, pid:nee502fe9ef46621421e0a17d05def099a62e77f 

        echo -e "\ndu /ramshare/ -d 1"
        du /ramshare/ -d 1

        echo -e "\nlsof"
        lsof

        echo -e "\nps -T"
        ps -T
        echo -e "\n=============================== RAMDISK END ================================\n"
	
        echo -e "\n=======================tar cpu use rate files into oss_cpu_log.tar.gz==============\n"
        tar -czf ./oss_cpu_log.tar.gz /logs/OssLog/OssCpuLog
        echo -e "\n=============================== TAR CPU LOG END ================================\n"

        echo -e "\n=============================== VMALLOC BEGIN ================================\n"
        echo -e "\nvmallocinfo"
        cat /proc/vmallocinfo
        echo -e "\nvmalloctotal"
        grep vmalloc /proc/vmallocinfo | awk '{total+=$2}; END {print total}'
        echo -e "\n=============================== VMALLOC END ================================\n"

        echo -e "\ncat /proc/slabinfo"
        cat /proc/slabinfo
        cat /proc/buddyinfo
        cat /proc/pagetypeinfo


        echo -e "\n=============================== KILL USHELL BEGIN ================================\n"
        echo -e "\nkill ushell"
        for line in $(ps |grep ushell |grep -v "grep" |awk '{print $1}');
        do
            kill -9 $line
        done
        echo -e "\n=============================== KILL USHELL END ================================\n"


        echo "@@@@@@@@@@@@@@@@@@@@Begin  HWM"
        echo -e "\n=============================== HWM PS BEGIN ================================\n"
        ps | grep "HWM.EXE" | grep -v "grep"
        echo "Starting collect ${PLAT_PID}"
        echo -e "\n=============================== HWM PS END ================================\n"
        get_proc_proc ${PLAT_PID} "HWM"
        echo -e "\n=============================== HWM SDRVersion BEGIN ================================\n"
        echo -e "\nSDRVersion in ${PLAT_PID} process"
        /ushell -NoBreak -pad ${PLAT_PID} -t 2000  -c "SDRVersion"
        echo -e "\n=============================== HWM SDRVersion END ================================\n"
        get_proc_info ${PLAT_PID} "HWM"
        echo "@@@@@@@@@@@@@@@@@@@@End  HWM"



        for i in $(docker ps | awk '{print $1 " "  $2}' | sed -e "s/\(.*\) [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*:[0-9]*\/\(.*\):.*/\2:\1/" | grep -v "CONTAINER" | grep -v "init_c");
        do
                echo "@@@@@@@@@@@@@@@@@@@@Begin  ${i%%:*}" ;  
                container_name=${i%%:*}
                get_elf_name $container_name
                elf=$elf_name
                if [ 'x'$elf = 'x' ] ; then 
                        elf="${i%%:*}"
                fi

                if [ $elf = "ro" ] ; then
                    docker exec -u root -i -e neicun=$elf ${i#*:} sh -c 'source /oss/oss/vsw_mem_full.sh env;nnn=`env | grep neicun | cut -d \= -f 2`;get_ro_container_mem $nnn';
                elif [ $elf = "sh" ] ; then 
                    docker exec -u root -i -e neicun=$elf ${i#*:} sh -c 'source /oss/oss/vsw_mem_full.sh env;nnn=`env | grep neicun | cut -d \= -f 2`;get_sh_container_mem $nnn';
                elif [ $elf = "weblmt" ] ; then
                    echo -e "\n******************************* weblmt not support *******************************\n";
                elif [ $elf = "apmac" ] ; then
                    docker exec -u root -i -e neicun=$elf ${i#*:} sh -c 'source /oss/oss/vsw_mem_full.sh env;nnn=`env | grep neicun | cut -d \= -f 2`;get_apmac_container_mem $nnn';
                elif [ $elf = "webmnt" ] ; then
                    echo -e "\n******************************* webmnt not support *******************************\n";
                elif [ $elf = "lcs.exe" ] ; then
                    echo -e "\n******************************* lcs not support *******************************\n";
                elif [ $elf = "umf_task_manager.exe" ] ; then
                    echo -e "\n******************************* umf_task_manager not support *******************************\n";
                else
                    docker exec -u root -i -e neicun=$elf ${i#*:} sh -c 'source /oss/oss/vsw_mem_full.sh env;nnn=`env | grep neicun | cut -d \= -f 2`;get_container_mem $nnn';
                fi
                
                echo "@@@@@@@@@@@@@@@@@@@@End  ${i%%:*}" ;
        done
        echo -e "\n script version 20250207 \n"
        echo -e "\n******************************* MEM INFO END *******************************n"
        date
        55667788
fi

# Ended by AICoder, pid:oe4a8kc25db9a4414cb1097374806e91deb7dada