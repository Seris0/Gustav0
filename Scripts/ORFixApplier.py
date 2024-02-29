#Code fix and improved by golanah921
#Original idea by Nooble_

import os
charaname = ['Dori','Collei','Tighnari','Candace','Cyno','Nilou','Nahida','Layla','Faruzan','Wanderer','Alhaitham','YaoYao','Dehya','Mika','Baizhu','Kaveh','Kirara','Lyney','Lynette','Freminet','Neuvillette','Wriothesley','Furina','Charlotte','Navia','Chevreuse','Xianyun','GaMing','Gaming','AyakaSpring','LisaStudent','KaeyaSailwind','GanyuTwilight']
charapart = ['Body','Dress','Head','Extra','HatHead','JacketHead','JacketBody','HoodDownHead']
excludepart = ['TighnariFaceHead','CynoDress','CynoFaceHead','NilouFaceHead','MikaDress','LynetteHead','NeuvilletteHead','NeuvilletteDress','FurinaDress','GanyuTwilightDress','GanyuTwilightBody','AyakaSpringDress','KaeyaSailwindHead','KaeyaSailwindDress']
checklist =[]
for r, d, f in os.walk(".\\"):
    for file in f:
        if file.endswith(".ini") and not file.endswith ("merged.ini"):
            print(".ini file found!: " + os.path.join(r, file))
            try:
                openFile = open(os.path.join(r, file), "r")
                lines = openFile.readlines()
                override = False
                lineNumber = 0
                for name in charaname:
                #check ini name for charaname
                    if name in file:
                        checklist.clear()
                        #create checklist
                        for part in charapart:
                            checklist.append(name+part)
                            #exclude part that need to be excluded from checklist
                            for exclude in excludepart:
                                if exclude in checklist:
                                    checklist.remove(exclude)
                        for i in lines:
                            for checkitem in checklist:
                                if i.startswith("[TextureOverride"+checkitem):
                                    override = True
                                if i == "run = CommandList\global\ORFix\ORFix\n":
                                    override = False
                                if override == True:
                                    if i == "\n":
                                        lines[lineNumber] = "run = CommandList\global\ORFix\ORFix\n\n"
                                        override = False
                            lineNumber += 1
                openFile.close()
                writeFile = open(os.path.join(r, file), "w")
                newFile = ""
                for i in lines:
                    newFile += i
                writeFile.write(newFile)
                writeFile.close()
            except:
                print("Something went wrong!")
