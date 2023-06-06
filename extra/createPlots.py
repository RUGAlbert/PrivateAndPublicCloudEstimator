import matplotlib.pyplot as plt
import numpy as np



def start():
    xpoints = np.array(range(1,175))
    ypoints = 1/np.power(0.0026 * xpoints, 1.6)
    # ypoints = 1/xpoints

    # plt.plot(xpoints, ypoints, xlabel="amount of max users per hour", ylabel="")
    fig, ax = plt.subplots()
    ax.plot(xpoints, 1/np.power(0.0026 * xpoints, 1))
    ax.plot(xpoints, 1/np.power(0.0026 * xpoints, 1.5))
    ax.plot(xpoints, 1/np.power(0.0026 * xpoints, 2))
    plt.xlabel("amount of max users per hour")
    plt.ylabel("power consumption per user in watt")
    # ax.fill_between(xpoints, ypoints, 0, color='blue', alpha=.1)
    plt.show()
    
