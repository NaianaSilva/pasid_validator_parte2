import matplotlib.pyplot as plt
from graphs import plot_mrt

def generate_graph(times):
    plt.plot(times, label='Tempo de Resposta (s)')
    plt.xlabel('Requisição')
    plt.ylabel('Tempo (s)')
    plt.title('MRT - Mean Response Time')
    plt.legend()
    plt.grid(True)
    plt.show()
    
