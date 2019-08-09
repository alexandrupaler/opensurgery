import json

from resanalysis.cube_to_physical import Qentiana
from resanalysis.experiment import Experiment

from resanalysis.distance_bins import  DistanceBins
from resanalysis.phys_qubits_vs_log_err import PhysicalQubitsVsLogicalError
from resanalysis.time_vs_space import TimeVsSpace
from resanalysis.res_savings import ResourceSavings

def main():
    ex1 = Experiment()
    ex1.props["footprint"] = 10
    ex1.props["t_count"] = 100
    ex1.props["prefer_depth_over_t_count"] = False

    qentiana = Qentiana(ex1.props)
    res_values = qentiana.compute_physical_resources()
    print("Resource prediction: ", res_values)

    ex2 = Experiment()
    ex2.props["footprint"] = 10
    ex2.props["depth_units"] = 100
    ex2.props["prefer_depth_over_t_count"] = True
    # construct
    db = DistanceBins()
    params = {}
    data = db.gen_data(experiment=ex2.props, parameters=params)
    # print(data)

    # construct
    pqvle = PhysicalQubitsVsLogicalError()
    params = {"total_num_physical_qubits": 500}
    data = pqvle.gen_data(experiment=ex2.props, parameters=params)
    # print(data)

    # construct
    tvs = TimeVsSpace()
    params = {}
    data = tvs.gen_data(experiment=ex2.props, parameters=params)
    # print(data)

    # construct
    rs = ResourceSavings()
    params = {}
    data = rs.gen_data(experiment=ex2.props, parameters=params)
    # print(data)


if __name__ == "__main__":
    # Entry to main
    main()