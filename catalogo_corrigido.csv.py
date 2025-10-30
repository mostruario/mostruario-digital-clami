import pandas as pd
import os

# Caminho do CSV original (ajuste se necessário)
CSV_ORIGINAL = "catalogo.csv"
CSV_SAIDA = "catalogo_corrigido.csv"

# Lê o arquivo
df = pd.read_csv(CSV_ORIGINAL, dtype=str, encoding="utf-8").fillna("")

# Função para limpar o caminho da imagem
def corrigir_caminho(caminho):
    if not isinstance(caminho, str):
        return ""
    caminho = caminho.strip()
    # Se for caminho local tipo C:\projetos\catalogo_digital\imagens\00095\arquivo.jpg
    if "catalogo_digital" in caminho:
        partes = caminho.split("catalogo_digital")[-1].lstrip("\\/")  # remove tudo antes da pasta
        partes = partes.replace("\\", "/")  # troca barra invertida por barra normal
        return partes  # ex: imagens/00095/arquivo.jpg
    return caminho

# Aplica a função
df["imagem_url"] = df["imagem_url"].apply(corrigir_caminho)

# Salva o novo CSV corrigido
df.to_csv(CSV_SAIDA, index=False, encoding="utf-8")

print(f"✅ CSV corrigido salvo como: {CSV_SAIDA}")
print("Agora cada linha aponta para um caminho relativo tipo:")
print("imagens/00095/NOME_DA_IMAGEM.jpg")
