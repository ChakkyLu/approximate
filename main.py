from base.Implement import Implement
import sys


if __name__ == "__main__":


    print("-"*10 + "Only support two input blif as input" + "-"*10)

    Im = Implement()
    exsim = "Exhaustive Simulation"
    simeq = "Equivalence Checking between file1 and file2"
    approximate = "Generate approximate circuit"
    booth = "Generate Booth approximate multipliers"

    if len(sys.argv) <= 2:
        print("-"*10 + "Commands" + "-"*10)
        print(">>>>exsim filename : %s" % exsim)
        print(">>>>simeq filename1 filename2: %s " % simeq)
        print(">>>>approximate filename: %s " % approximate)
        print(">>>>booth filename: %s " % booth)

    else:
        command = sys.argv[1]

        if command == "exsim":
            if len(sys.argv) != 3:
                print(">>>>Please use as follows")
                print("exsim spec.blif")
            else:
                print(">>>Exhaustive simulation............")
                Im.GetMulDict(sys.argv[2])

        if command == "simeq":
            if len(sys.argv) != 4:
                print(">>>>Please use as follows")
                print("simeq spec.blif impl.blif")
            else:
                print(">>>Equivalence Checking............")
                Im.DoExSim(sys.argv[2], sys.argv[3])

        if command == "approximate":
            if len(sys.argv) != 3:
                print(">>>>Please use as follows")
                print("approximate spec.blif")
            else:
                print(">>>Generating approximate circuit............")
                Im.getApproCir(sys.argv[2])

        if command == "booth":
            if len(sys.argv) != 3:
                print(">>>>Please use as follows")
                print("ecsingle spec.blif")
            else:
                print(">>>>Generating the approximate booth multipliers........")
                Im.HeuForBooth(sys.argv[2])
