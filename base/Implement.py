# Approximate Algorithm

from .Circuit import Circuit
from collections import defaultdict
import time
import sys
sys.path.append("..")
from sat.genSAT import for_booth, buma, absolute, gen_pattern
import os
import math

class Implement:
    def __init__(self):
        # self.maps = {}
        pass
    # exhaustive simulation of file1 and file2
    def DoExSim(self, filename1, filename2):
        spec_cir = Circuit()
        spec_cir.readBlif(filename1)
        impl_cir = Circuit()
        impl_cir.readBlif(filename2)

        circuit_size = len(spec_cir.inputs)

        j = 0
        WM = 0
        WCAE = float("-inf")
        MAE = 0
        pattern = []
        o1, o2 = [], []

        for inputs in range(2**circuit_size):

            inputs = str(bin(inputs))[2:]
            inputs = '0'* (circuit_size - len(inputs)) + inputs

            outputs = spec_cir.simulate(inputs)
            outputs2 = impl_cir.simulate(inputs)
            if outputs != outputs2:
                WM += 1

            cur_WCAE = float(abs(int(outputs,2)-int(outputs2,2))/(2**len(spec_cir.outputs)))


            if cur_WCAE >= 0.000108:
                print(inputs)
                print(int(outputs,2))
                print(int(outputs2,2))
                pattern.append(inputs)
                o1.append(outputs)
                o2.append(outputs2)

            if len(pattern) > 5: break

            WCAE = max(WCAE, cur_WCAE)
            MAE += cur_WCAE
            sys.stdout.write("\rProgress: %d / %d" % (j+1, 2**circuit_size))
            j += 1

        MAE = float( MAE / (2**circuit_size) )

        print("Different Minterms: %s " % str(WM))
        print("Worst Case Absolute Error Rate : %s " % str(WCAE))
        print("Mean Absolute Error Rate  %s " % str(MAE))

    def GetMulDict(self, filename):
        spec_cir = Circuit()
        spec_cir.readBlif(filename)
        circuit_size = len(spec_cir.inputs)

        kdict = {}

        for i in range(2**32):
            kdict[i] = "0"*1

    def HeuForBooth(self, filename):
        # print("Please input status:")
        # print(">>> 1 : generate nodemap for booth multipliers")
        # print(">>> 2 : generate approximate booth multipliers")

        spec_cir = Circuit()
        spec_cir.readBlif(filename)
        circuit_size = len(spec_cir.inputs)
        size = spec_cir.size

        datapath = os.getcwd() + "/sub/"
        satpath = os.getcwd() + "/sat/"
        ap_path = os.getcwd() + "/approximate_circuit/"


        base_name = filename[filename.find("/")+1:filename.find(".")] + ".csv"
        print(base_name)


        print("Please input target error: ")
        target_err = float(input())
        cur_err = 0

        adder_name = "a%d.blif"%(circuit_size+1)

        try:
            fadder = open(satpath+adder_name).readlines()
        except:
            try:
                os.system("cd sat; ../abc-master/abc -c \"gen -a -N %d %s; strash; write %s\" " % (circuit_size+1, adder_name, adder_name))
                fadder = open(satpath+adder_name).readlines()
            except Exception as e:
                print("abc-master package is required.")
                return 0

        if "end" in fadder[-2]:
            adder_str =  "".join(fadder)
            adder_str = adder_str[adder_str.find(".names"):]
            adder_str = adder_str.replace("a","m").replace("b", "l").replace("new_n", "q").replace("nmmes", "names").replace(".end", "").replace("_","")
        else:
            adder_str =  "".join(fadder)


        spec_str = "".join(open(filename).readlines()[:])
        input_str = spec_str[:spec_str.find(".outputs")]
        spec_str = spec_str[spec_str.find(".names"):].replace(".end", "")

        input_str += ".outputs out\n"

        cur_time = time.time()

        def genMap():

            # base_name = f
            nodesMap_name = []
            nodesMap_type = []

            content = spec_cir.getStrOfCir()

            fwrite = open(datapath + "base.csv", 'w')

            fixed_file = satpath + filename[filename.find("/")+1:filename.find(".")] + "base.blif"

            under_m = for_booth(circuit_size, adder_str, circuit_size-1) + "\n.end"


            spec_cir.GetEachNodePriOut()


            for i in range(len(spec_cir.nodes)):

                o_node = content[i]
                node = spec_cir.nodes[i].copy()
                spec_cir.nodes[i].badstatus = 0

                if node.name in spec_cir.outputs:
                    fwrite.write(node.name+","+str(float(2**int(node.name[1:])/(2**len(spec_cir.outputs))))+"\n")
                else:
                    if node.inputs[0].name in spec_cir.inputs and node.inputs[1].name in spec_cir.inputs and  node.inputs[0].name[0] == node.inputs[1].name[0]:
                        spec_cir.nodes[i].badstatus = 1
                        continue
                    if node.inputs[1].badstatus == 1 and node.inputs[0].name not in spec_cir.inputs:
                        spec_cir.nodes[i].badstatus = 1
                        continue
                    err = 2 ** (spec_cir.poInfo[node.name]-len(spec_cir.outputs))

                    fw = open(fixed_file, 'w')
                    node.inputs = []
                    node.type = "ZERO"
                    fw.write(input_str+spec_str)
                    content[i] = node.singleMSG()
                    fw.write("".join(content))
                    fw.write(under_m)
                    fw.close()

                    os.system('cd sat; ../abc-master/abc -c \" read '+fixed_file+'; sat; \" > log1')
                    flog = open(satpath+"log1").readlines()[-1]

                    if "UNSATISFIABLE" in flog:
                        fwrite.write(node.name+","+"0"+","+str(err)+"\n")
                        continue

                    node.inputs = []
                    node.type = "ONE"
                    fw = open(fixed_file, 'w')
                    content[i] = node.singleMSG()
                    fw.write(input_str+spec_str)
                    fw.write("".join(content))
                    fw.write(under_m)
                    fw.close()

                    os.system('cd sat; ../abc-master/abc -c \" read '+fixed_file+'; sat; \" > log2')
                    flog = open(satpath+"log2").readlines()[-1]
                    if "UNSATISFIABLE" in flog:
                        fwrite.write(node.name+","+"1"+","+str(err)+"\n")


                    content[i] = o_node

            fwrite.close()

            print(">>>It takes %s \'s to generate node map" % str(time.time()-cur_time))

        def getBooth(basefile):
                fbase = open(basefile).readlines()
                content = spec_cir.getStrOfCir()

                # origina_content = content.deepcopy()

                selected = []
                nnwithvalue = {}

                nodeMap = [(fcontent.split(",")[0], fcontent.split(",")[1], float(fcontent.split(",")[2])) for fcontent in fbase]
                nodeMap = sorted(nodeMap, key=lambda x:x[2])

                adder_name = "a%d.blif"%(circuit_size+1)


                where = math.ceil(math.log(target_err*(2**len(spec_cir.outputs)),2))
                under_m = for_booth(circuit_size, adder_str, where) + "\n.end"


                for nmap in nodeMap:
                    nnwithvalue[nmap[0]] = nmap[2]
                    node = spec_cir.nodeMaps[nmap[0]].copy()
                    node_p = spec_cir.find(node.name)
                    if (node.inputs[0].name in spec_cir.inputs) or (node.inputs[0].name in selected and node.inputs[1].name in selected):
                        if (cur_err+nmap[2]) <= target_err:
                            if spec_cir.nodeMaps[nmap[0]].inputs[0].name in selected:
                                cur_err -= nnwithvalue[spec_cir.nodeMaps[nmap[0]].inputs[0].name]
                            else:
                                if spec_cir.nodeMaps[nmap[0]].inputs[1].name in selected:
                                    cur_err -= nnwithvalue[spec_cir.nodeMaps[nmap[0]].inputs[1].name]

                            cur_err += nmap[2]
                            content[node_p] = node.typeChange(int(nmap[1]))
                            spec_cir.ModifyCir(nmap[0], int(nmap[1]))
                            selected.append(nmap[0])

                            fw = open(satpath+"forsat.blif", 'w')
                            fw.write(spec_str+"".join(content)+under_m)
                            fw.close()

                            os.system('abc-master/abc -c -c \" read %s; resyn2; sat; \" > log' % (satpath+"forsat.blif"))
                            flog = open("log").readlines()[-1]

                            # print(flog)
                            if "UNSATISFIABLE" in flog:
                                selected.append(nmap[0])
                                pass
                            else:
                                spec_cir.nodes[node_p] = node.copy()
                                content[node_p] = node.strOfGate()
                                cur_err -= nmap[2]


                print(">>>It takes %s \'s to generate approximate circuits" % str(time.time()-cur_time))
                spec_cir.writeBlif(ap_path+ + filename[filename.find("/")+1:filename.find(".")] + "ap.blif")
        try:
            open(datapath+base_name)
            getBooth(datapath+base_name)
        except:
            print("Generating nodemap.........")
            genMap()
            getBooth(datapath+base_name)





        print(">>>It takes %s \'s " % str(time.time()-cur_time))
    # exhaustive simulation of spec_cir and impl_cir
    def DoExSimCir(self, spec_cir, impl_cir):
        circuit_size = len(spec_cir.inputs)

        WM = 0
        WCAE = float("-inf")
        MAE = 0
        j = 0

        for inputs in range(2**circuit_size):

            inputs = str(bin(inputs))[2:]
            inputs = '0'* (circuit_size - len(inputs)) + inputs

            outputs = spec_cir.simulate(inputs)
            outputs2 = impl_cir.simulate(inputs)
            if outputs != outputs2:
                WM += 1

            # print(outputs, outputs2)

            WCAE = max(WCAE, float(abs(int(outputs,2)-int(outputs2,2))/(2**len(spec_cir.outputs))))
            MAE += float(abs(int(outputs,2)-int(outputs2,2))/ (2**len(spec_cir.outputs)))
            # sys.stdout.write("\rProgress: %d / %d" % (j+1, 2**circuit_size))
            j += 1
        MAE = float( MAE / (2**circuit_size) )

        # print("DIFFERENT MINTERMS: %s " % str(WM))
        print("Worst Case Absolute Error is : %s " % str(WCAE))
        print("Mean Absolute Error Rate is : %s " % str(MAE))

    def simplify(self, filename1):
        spec_cir = Circuit()
        spec_cir.readBlif(filename1)
        spec_cir.AIGtoXOR()
        save_path = filename1
        # os.path.abspath(os.path.join(os.getcwd(), "..")) + "/database/" + spec_cir.model.lower()+"c.blif"
        spec_cir.writeBlif(save_path)

    def Heuristic(self, filename1, filename2):
        start_time = int(time.time())
        spec_cir = Circuit()
        spec_cir.readBlif(filename1)
        impl_cir = Circuit()
        impl_cir.readBlif(filename2)

        circuit_size = len(spec_cir.inputs)
        size = int(circuit_size/2)

        j = 0
        WM = 0
        WCAE = float("-inf")
        MAE = 0
        pattern = []
        o1, o2 = [], []
        val = 0
        #
        print("Simulation.....")
        status = 1

        if status == 0:
            inputs_s = [0]*size + [0]*size
            inputs_s[int(0)] = 1
            inputs_s[size+int(7)] = 1
            # inputs_s[size+int(1)] = 1
            inputs_s = inputs_s[:size][::-1] + inputs_s[size:][::-1]

            inputs_s = "".join( list(map(str,inputs_s)) )

            print(inputs_s)

            for inputs in ["1"*(size*2)]:
                # inputs += "01"+""
                # inputs = str(bin(inputs))[2:]
                # inputs = "0"*(size-1-len(inputs)) + inputs
                # # inputs = "0"*size + inputs
                # inputs = inputs[:size-2] + "1" + inputs[:size-1] + inputs + "1"


                outputs = spec_cir.simulate(inputs)

                outputs2 = impl_cir.simulate(inputs)



                # outputs_c = str(bin(int("0"*1+"1"*15,2) * int("1"*16,2)))[2:]
                # outputs_c = int(inputs[:8],2) + int(inputs[8:],2)

                # print(outputs,outputs2, str(bin(outputs_c)))
                # print(int(outputs,2),int(outputs2,2))

                # print(outputs,outputs2)


                cur_WCAE = float(abs(int(outputs,2)-int(outputs2,2))/(2**len(spec_cir.outputs)))
                WCAE = max(cur_WCAE, WCAE)


                # print(inputs[0]=="1")
                if cur_WCAE > 0.9:
                    break

            print("worst case asbsolute error rate : %s " % str(WCAE))

        if status == 1:

            tmp = 0
            for inputs in range(2**circuit_size):

                inputs = str(bin(inputs))[2:]

                inputs = '0'* (circuit_size - len(inputs)) + inputs

                # if inputs[:size] == "0"*size or inputs[size:] == "0"*size:
                #     continue

                outputs, dict1 = spec_cir.simulate(inputs)
                # outputs = str(bin(abs(int(inputs[:size],2) * int(inputs[size:],2))))[2:]
                # outputs = '0'*(circuit_size-len(outputs)) + outputs
                outputs2, dict2 = impl_cir.simulate(inputs)
                # print(int(inputs[:int(len(inputs)/2)],2), int(inputs[int(len(inputs)/2):],2), int(outputs, 2), int(outputs2, 2))

                # if outputs != outputs2:
                #     WM += 1
                #     if  int(outputs,2)-int(outputs2,2) == 25:
                #         print(inputs, int(outputs,2), int(outputs2,2), int(outputs,2)-int(outputs2,2))
                #         print(outputs, outputs2)
                    # break

                cur_WCAE = float(abs(int(outputs[:],2)-int(outputs2[:],2))/(2**circuit_size))

                if cur_WCAE > 3.0517e-05 and outputs[-1] == "1":
                    print(outputs[:],outputs2[:])
                # print(inputs, int(outputs[:size],2), abs(int(outputs2[:size],2)))
                if int(outputs[:size],2) < int(outputs2[:size],2):
                    val += 1

                    # if (inputs[5]== "1" and inputs[-3]=="1"):
                        # print(inputs[5], inputs[-3])
                        # print(inputs, int(outputs[:size],2), abs(int(outputs2[:size],2)))
                        # tmp += 1
                    # if outputs[:4] == outputs2[:4]:
                        # print(inputs,outputs[4:],outputs2[4:])
                    pattern.append(inputs)
                    o1.append(outputs)
                    o2.append(outputs2)


                WCAE = max(WCAE, cur_WCAE)
                MAE += cur_WCAE
                # sys.stdout.write("\rProgress: %d / %d" % (j+1, 2**circuit_size))
                j += 1

                MAE = float( MAE / (2**circuit_size) )

            print("DIFFERENT MINTERMS: %s " % str(WM))
            # print(val,tmp)
            print("worst case absolute error rate : %s " % str(WCAE))
            print("worst case absolute error %s " % str(WCAE*(2**circuit_size)))
            print("================")
            # print(len(pattern))
            # print(pattern,o1,o2)
            print("Program Cost: %s 's " % str( float(time.time() - start_time)) )

    def getApproCir(self, filename):
        print("Pleas input target err")

        target_err = float(input())
        cur_time = time.time()
        spec_cir = Circuit()
        spec_cir.readBlif(filename)

        ap_err = spec_cir.GetBasicPattern()

#
        # BESTCHOICE = {"AND": 0, "OR": 1, "XOR": 2, "XNOR":4, "NOR": 0, "AND2_PN":0, "AND2_NP":0, "NAND2_PN":1, "NAND2_NP":1}
        impl_cir = spec_cir.copy()
        nodes = spec_cir.nodes


        cur_err = 0
        cur_nodes = []
        i = 0

        ap_err = sorted(ap_err.items(), key=lambda kv: kv[1]["err"])


        for case in ap_err:
            node_p = impl_cir.find_node(case[0])
            if node_p != -1:
                if cur_err >= target_err:
                    break
                if not impl_cir.nodes[node_p].inputs[0].inputs or len(impl_cir.nodes[node_p].inputs[0].inputs) < 2:
                    cur_err += case[1]["err"]
                impl_cir.ModifyCir(case[0], 0)


        cur_time = time.time() - cur_time

        save_path =  spec_cir.model.lower() + "ap.blif"
        # save_path = os.path.abspath(os.path.join(os.getcwd(), "..")) + "/approximate_circuit/" + spec_cir.model.lower()+"_ap.blif"
        print("\n"+"It takes " + str(cur_time) + " 's to generate approximate circuits")
        impl_cir.writeBlif(save_path)
        # self.DoExSimCir(spec_cir, impl_cir)
    def verify(self, filename1, filename2, target_err):
        spec_cir = Circuit()
        spec_cir.readBlif(filename1)

        impl_cir = Circuit()
        impl_cir.readBlif(filename2)

        target_err = float(target_err)

        input_size = len(spec_cir.inputs)
        output_size = len(spec_cir.outputs)

        if len(impl_cir.inputs) != input_size or len(impl_cir.outputs) != len(spec_cir.outputs):
            print("I/O are different!")
            return 0

        impl_str = "".join(open(filename2).readlines()[:])
        impl_str = impl_str[impl_str.find(".names"):]
        impl_str = impl_str.replace("n", "j").replace("james", "names").replace("ijputs", "inputs").replace(".ejd", "")
        impl_str = impl_str.replace("m", "k").replace("nakes", "names")

        spec_str = "".join(open(filename1).readlines()[:])
        input_str = spec_str[:spec_str.find(".outputs")]
        spec_str = spec_str[spec_str.find(".names"):].replace(".end", "")

        input_str += ".outputs out\n"

        fw = open("verify.blif", "w")

        fw.write(input_str)
        fw.write("#G\n"+spec_str)
        fw.write("#C\n"+impl_str)

        adder_name = "a%d.blif" % (input_size+1)

        try:
            os.system("abc-master/abc -c \"gen -a -N %d %s; strash; write %s\" " % (input_size+1, adder_name, adder_name))
        except Exception as e:
            print("abc-master package is required.")


        # adder = Circuit()
        # adder.readBlif("a%d.blif" % input_size+1)


        adder_str = "".join(open(adder_name).readlines()[:])
        adder_str = adder_str[adder_str.find(".names"):]
        adder_str = adder_str.replace("a","m").replace("b", "l").replace("new_n", "q").replace("nmmes", "names").replace(".end", "").replace("_","")

        datapath = os.getcwd() + "/sat/"

        fadder = open(datapath+adder_name, "w")
        fadder.write(adder_str)
        fadder.close()


        fw.write("#COM\n"+buma(output_size))
        fw.write("#SUB\n"+adder_str)
        fw.write("#ABSOLUTE\n"+absolute(output_size))
        # final_ver +=  buma(output_size) + adder_str + absolute(adder_str)

        give_pattern = ""

        for i in range(output_size):
            tmp = 2**(-i-1)
            if target_err >= tmp:
                give_pattern += "1"
                target_err -= tmp
            else:
                give_pattern += "0"
            if target_err < 2 ** (-output_size):
                break

        fw.write(gen_pattern(give_pattern, output_size) + ".end\n")
        fw.close()
        # final_ver += gen_pattern(give_pattern, output_size) + ".end\n"

        try:
            f = open("abc.rc")
        except:
            os.system("cp abc-master/abc.rc abc.rc")

        # os.system("/abc-master/abc -c\"gen -a %d a%d.blif\" " % (input_size+1, input_size+1))
        os.system('abc-master/abc -c \" read verify.blif; resyn2; sat; \" > log')
        flog = open("log").readlines()[-1]
        print("-"*10+"SAT RESULT"+"-"*10+"\n"+flog+"-"*30)

        if "UNSATISFIABLE" in flog:
            print("The error of given circuit is !within! target error")
            print("PASS!")
        else:
            print("The error of given circuit is !greater! than target error")
            print("FAIL!")

        # os.system("rm a*blif; rm *log")
