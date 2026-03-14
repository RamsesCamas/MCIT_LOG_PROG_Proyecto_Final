import pandas as pd
import matplotlib.pyplot as plt
import os

def leer_datos():
    base_dir = os.path.dirname(__file__)
    ruta_csv = os.path.join(base_dir, "..", "benchmarks", "results.csv")
    df = pd.read_csv(ruta_csv)
    return df

def validar_columnas(df):
    columnas_necesarias = [
        "n",
        "t_p",
        "t_q_async",
        "t_q_full",
        "speedup_async",
        "speedup_full"
    ]

    for columna in columnas_necesarias:
        if columna not in df.columns:
            raise ValueError(f"Falta la columna: {columna}")

def obtener_carpeta_salida():
    return os.path.dirname(__file__)

def calcular_throughput(df):
    df["throughput_p"] = df["n"] / df["t_p"]
    df["throughput_q_async"] = df["n"] / df["t_q_async"]
    df["throughput_q_full"] = df["n"] / df["t_q_full"]
    return df

def graficar_speedup(df,carpeta_salida):
    plt.figure(figsize=(8, 5))
    plt.plot(df["n"], df["speedup_async"], marker="o", label="AsyncIO only")
    plt.plot(df["n"], df["speedup_full"], marker="o", label="AsyncIO+MP")

    plt.title("Speedup vs Tamaño del problema (n)")
    plt.xlabel("Número de intersecciones (n)")
    plt.ylabel("Speedup")
    plt.legend()
    plt.grid(True)

    ruta_guardado = os.path.join(carpeta_salida, "speedup_vs_n.png")
    plt.savefig(ruta_guardado)
    plt.close()

def graficar_tiempos(df, carpeta_salida):
    x = range(len(df))
    ancho = 0.25

    plt.figure(figsize=(10, 5))
    plt.bar([i - ancho for i in x], df["t_p"], width=ancho, label="P")
    plt.bar(x, df["t_q_async"], width=ancho, label="Q-async")
    plt.bar([i + ancho for i in x], df["t_q_full"], width=ancho, label="Q-full")

    plt.title("Comparación de tiempos de ejecución")
    plt.xlabel("Número de intersecciones (n)")
    plt.ylabel("Tiempo de ejecución (s)")
    plt.xticks(list(x), df["n"])
    plt.legend()
    plt.grid(True, axis="y")

    ruta_guardado = os.path.join(carpeta_salida, "tiempos_comparativa.png")
    plt.savefig(ruta_guardado)
    plt.close()

def graficar_throughput(df, carpeta_salida):
    plt.figure(figsize=(8, 5))
    plt.plot(df["n"], df["throughput_p"], marker="o", label="P")
    plt.plot(df["n"], df["throughput_q_async"], marker="o", label="Q-async")
    plt.plot(df["n"], df["throughput_q_full"], marker="o", label="Q-full")

    plt.title("Throughput vs Tamaño del problema (n)")
    plt.xlabel("Número de intersecciones (n)")
    plt.ylabel("Intersecciones por segundo")
    plt.legend()
    plt.grid(True)

    ruta_guardado = os.path.join(carpeta_salida, "throughput_vs_n.png")
    plt.savefig(ruta_guardado)
    plt.close()


def main():
    datos = leer_datos()
    validar_columnas(datos)
    print("\ncsv original\n")
    print(datos)
    datos = calcular_throughput(datos)
    print("\nAñadiendo las columnas con los calculos del throughput \n")
    print(datos)

    carpeta_salida = obtener_carpeta_salida()

    graficar_speedup(datos, carpeta_salida)
    graficar_tiempos(datos, carpeta_salida)
    graficar_throughput(datos, carpeta_salida)
    print("Las 3 gráficas se generaron correctamente")

if __name__ == "__main__":
    main()