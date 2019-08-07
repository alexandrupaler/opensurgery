import math


# def analysis(data, experiment):
#     """
#
#     :param data:
#     :param experiment:
#     :return:
#     """
#
#     ## The parameters from experiment are scaled using data
#     # the new volume
#     volume_scale = data.y
#     scaled_volume = approx_mult_factor(data.y, experiment.volume)
#
#     qre1 = qre.Qentiana(t_count = 0,
#                         max_logical_qubits = experiment.footprint,
#                         max_time_units = scaled_volume / experiment.footprint,
#                         gate_err_rate = experiment.physical_error_rate)
#
#     # for a volume of size scaled_volume, what is the distance?
#     recalc = qre1.compute_physical_resources()
#
#     # the computed distance is less than the scaling factor
#     is_fine = (recalc["distance"] <= volume_scale)
#
#     ret = {
#         "dist"      : recalc["distance"],
#         "ok"        : is_fine,
#         "threshold" : volume_scale,
#         "volume"    : scaled_volume
#     }
#
#     return ret


# def approx_mult_factor(factor, value):
#     return math.ceil(factor * value)

# TODO: replace with numpy calls
def local_logspace(start, stop, num = 50):
    # Assume base = 10
    ret = [0] * num
    delta = (stop - start) / num

    for i in range(num):
        ret[i] = math.pow(10, start + delta * i)

    return ret


#TODO: replace with numpy calls
def local_linspace(start, stop, num = 50):
    ret = [0] * num
    delta = (stop - start) / num

    for i in range(num):
        ret[i] = start + delta * i

    return ret

#TODO: replace with numpy calls
def local_linspace_2(middle, plus_minus_range, num = 50):
    # assume num is odd
    if num % 2 == 0:
        #make odd
        num += 1

    ret = [0] * num
    middle_index = math.floor(num / 2)
    ret[middle_index] = middle

    float_ratio = (2 * plus_minus_range) / num
    half_distance = middle_index

    for i in range(1, half_distance + 1):
        ret[middle_index + i] = middle + i * float_ratio
        ret[middle_index - i] = middle - i * float_ratio

    return ret

"""
    RGB functions for the interpretation of a value to integers in range 0..255
"""
def to_rgb(param):
    return (255 if (param > 1) else math.round(param * 255))

def from_rgb(param):
    # why is 2 here?
    return 2 if (param == 255) else (param / 255.0)

