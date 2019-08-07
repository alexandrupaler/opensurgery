import json

from resanalysis.cube_to_physical import Qentiana
from resanalysis.phys_qubits_vs_log_err import PhysicalQubitsVsLogicalError
from resanalysis.time_vs_space import TimeVsSpace
from resanalysis.res_savings import ResourceSavings

def main():
    jsonstr = '{"Chem 250": {\
                        "volume": 756142777500,\
                        "footprint": 512,\
                        "depth": 1,\
                        "physical_error_rate": 0.001,\
                        "routing_overhead": 50,\
                        "bool_distance": true,\
                        "enforced_distance": 24.7,\
                        "safety_factor": 9900\
                        }' \
              '}'
    expr = json.loads(jsonstr)["Chem 250"]

    qentiana = Qentiana(t_count=100, max_logical_qubits=10)
    res_values = qentiana.compute_physical_resources()
    print("Resource prediction: ", res_values)

    # construct
    pqvle = PhysicalQubitsVsLogicalError()
    params = {"total_num_physical_qubits": 500}
    data = pqvle.gen_data(experiment=expr, parameters=params)
    # print(data)

    # construct
    tvs = TimeVsSpace()
    params = {}
    data = tvs.gen_data(experiment=expr, parameters=params)
    # print(data)

    # construct
    rs = ResourceSavings()
    params = {}
    data = rs.gen_data(experiment=expr, parameters=params)
    # print(data)


if __name__ == "__main__":
    # Entry to main
    main()