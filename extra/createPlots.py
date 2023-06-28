import matplotlib.pyplot as plt
import numpy as np



def start():
    xpoints = np.array(range(10,2000))
    ypoints = 1/np.power(0.0026 * xpoints, 1.2)
    # ypoints = 1/xpoints

    # plt.plot(xpoints, ypoints, xlabel="amount of max users per hour", ylabel="")
    fig, ax = plt.subplots()
    ax.plot(xpoints, 1/np.power(0.0026 * xpoints, 1))
    ax.plot(xpoints, 1/np.power(0.0026 * xpoints, 1.5))
    ax.plot(xpoints, 1/np.power(0.0026 * xpoints, 2))
    ax.legend(["N-value of 1", "N-value of 1.5", "N-value of 2"],loc="upper right")
    
    # ax.axvline(x=30, color='y')
    plt.xlabel("amount of max users per hour")
    plt.ylabel("power consumption per user in watt")
    # ax.fill_between(xpoints, ypoints, 0, color='blue', alpha=.1)
    plt.show()
    
