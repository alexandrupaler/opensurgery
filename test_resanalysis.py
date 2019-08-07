import json

from resanalysis import cube_to_physical
from resanalysis import phys_qubits_vs_log_err
from resanalysis import time_vs_space
from resanalysis import res_savings

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

    qentiana = cube_to_physical.Qentiana(t_count=100, max_logical_qubits=10)
    res_values = qentiana.compute_physical_resources()
    print("Resource prediction: ", res_values)

    # construct
    pqvle = phys_qubits_vs_log_err.PhysicalQubitsVsLogicalError()
    params = {"total_num_physical_qubits": 500}
    data = pqvle.gen_data(experiment=expr, parameters=params)
    # print(data)

    # construct
    tvs = time_vs_space.TimeVsSpace()
    params = {}
    data = tvs.gen_data(experiment=expr, parameters=params)
    # print(data)

    # construct
    rs = res_savings.ResourceSavings()
    params = {}
    data = rs.gen_data(experiment=expr, parameters=params)
    # print(data)


if __name__ == "__main__":
    # Entry to main
    main()