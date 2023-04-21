import cloudflareDNS
import godaddyDNS
import huaweiDNS
import leacloudDNS
import nsone

def doUpdate(targetDomain):
    godaddyDNS.updateGodaddyDNS(targetDomain)
    cloudflareDNS.updateCloudflareDNS(targetDomain)
    nsone.updateNsoneDNS(targetDomain)
    leacloudDNS.main()

if __name__ == "__main__":
    doUpdate('')
