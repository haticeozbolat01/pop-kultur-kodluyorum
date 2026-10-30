"""Netflix İzleme Panom: kendi izleme geçmişini tıklanabilir bir panoya çeviren Streamlit uygulaması.

Çalıştırmak için:  streamlit run app.py
"""
import re

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Netflix İzleme Panom", page_icon="🎬", layout="wide")

MURDUM, SEFTALI, BOGURTLEN = "#2B1036", "#F6B17A", "#C2185B"
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
SEZON = re.compile(
    r"^(Sezon|Season|Bölüm|Episode|Kısıtlı Dizi|Limited Series|Mini Dizi|Kitap|Book|"
    r"Part|Kısım|Volume|Class|Chapter|Collection)\b",
    re.IGNORECASE,
)


# ---------- 1. Bölümdeki temizleme fonksiyonları ----------
def tarihi_coz(seri):
    ornek = seri.dropna().astype(str)
    if ornek.str.contains(r"\.").any():
        return pd.to_datetime(seri, format="%d.%m.%Y", errors="coerce")
    parca = ornek.str.split("/")
    gun_once = parca.str[0].astype(int).gt(12).any()
    yil_iki_hane = parca.str[-1].str.len().eq(2).all()
    if gun_once:
        bicim = "%d/%m/%y" if yil_iki_hane else "%d/%m/%Y"
    else:
        bicim = "%m/%d/%y" if yil_iki_hane else "%m/%d/%Y"
    return pd.to_datetime(seri, format=bicim, errors="coerce")


def ayir(baslik):
    parcalar = baslik.split(": ")
    for i, parca in enumerate(parcalar[1:], start=1):
        if SEZON.match(parca):
            return ": ".join(parcalar[:i]), "Dizi"
    return baslik, "Film"


@st.cache_data
def veriyi_hazirla(ham):
    df = ham.rename(columns={"Title": "baslik", "Date": "tarih"})
    df["tarih"] = tarihi_coz(df["tarih"])
    df = df.dropna(subset=["tarih"])
    df[["isim", "tur"]] = df["baslik"].apply(lambda b: pd.Series(ayir(b)))

    on_ek = df["baslik"].str.split(": ").str[0].str.strip()
    tekrar = on_ek.map(on_ek.value_counts())
    dizi_mi = (df["tur"] == "Film") & df["baslik"].str.contains(": ") & (tekrar >= 2)
    df.loc[dizi_mi, "isim"] = on_ek[dizi_mi]
    df.loc[dizi_mi, "tur"] = "Dizi"
    return df


@st.cache_data
def ornek_veri():
    """Dosya yüklenmediğinde gösterilen hayali veri (gerçek kişiye ait değildir)."""
    rng = np.random.default_rng(42)
    diziler = {"Uzay Kafesi": 24, "Kasabanın Sırrı": 16, "Mutfak Savaşları": 40, "Gece Nöbeti": 10}
    satirlar = [f"{d}: Sezon {1 + b // 10}: Bölüm {b % 10 + 1}" for d, n in diziler.items() for b in range(n)]
    satirlar += ["Gece Treni", "Son Mektup", "Kayıp Harita", "Dağdaki Ev", "Kırmızı Bisiklet"]
    tarihler = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 650, len(satirlar)), unit="D")
    return pd.DataFrame({"Title": satirlar, "Date": tarihler.strftime("%m/%d/%y")})


def cubuk(veri, x, y, renk=BOGURTLEN, sira=None, x_baslik="", y_baslik="Kayıt"):
    return (
        alt.Chart(veri)
        .mark_bar(color=renk, cornerRadiusEnd=4)
        .encode(
            x=alt.X(x, sort=sira, title=x_baslik, axis=alt.Axis(format="%m.%Y") if x.endswith(":T") else alt.Axis(labelAngle=0)),
            y=alt.Y(y, title=y_baslik, axis=alt.Axis(format="d")),
            tooltip=[x, y],
        )
    )


# ---------- 2. Veriyi al ----------
st.title("🎬 Netflix İzleme Panom")
st.caption("Netflix izleme geçmişini yükle; dosyan hiçbir yere kaydedilmez, sadece bu sayfada işlenir.")

dosya = st.file_uploader("NetflixViewingHistory.csv dosyanı yükle", type="csv")
if dosya is None:
    st.info("Henüz dosya yüklemedin. Aşağıda hayali bir örnek veriyle gösteriyorum.")
    df = veriyi_hazirla(ornek_veri())
else:
    df = veriyi_hazirla(pd.read_csv(dosya))

# ---------- 3. Filtreler ----------
with st.sidebar:
    st.header("Filtreler")
    yillar = sorted(df["tarih"].dt.year.unique())
    secilen_yillar = st.multiselect("Yıl", yillar, default=yillar)
    tur = st.radio("Tür", ["Hepsi", "Dizi", "Film"], horizontal=True)

f = df[df["tarih"].dt.year.isin(secilen_yillar)]
if tur != "Hepsi":
    f = f[f["tur"] == tur]
if f.empty:
    st.warning("Bu filtrelerle hiç kayıt yok. Soldan başka bir yıl ya da tür seç.")
    st.stop()

# ---------- 4. Özet kartlar ----------
gunluk = f.groupby(f["tarih"].dt.date).size()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Toplam kayıt", f"{len(f):,}".replace(",", "."))
k2.metric("Farklı dizi", f.loc[f["tur"] == "Dizi", "isim"].nunique())
k3.metric("Film", int((f["tur"] == "Film").sum()))
k4.metric("Maraton günü", f"{gunluk.max()} kayıt", help=f"En çok kayıt olan gün: {gunluk.idxmax()}")

# ---------- 5. Grafikler ----------
st.subheader("Aylara göre izleme")
aylik = f.groupby(f["tarih"].dt.to_period("M")).size().rename("Kayıt").reset_index()
aylik["Ay"] = aylik["tarih"].dt.to_timestamp()
st.altair_chart(cubuk(aylik, "yearmonth(Ay):T", "Kayıt:Q", x_baslik="Ay"), width="stretch")

sol, sag = st.columns(2)
with sol:
    st.subheader("Haftanın günleri")
    gunler = (
        f["tarih"].dt.dayofweek.map(lambda i: GUNLER[i]).value_counts()
        .reindex(GUNLER, fill_value=0).rename_axis("Gün").reset_index(name="Kayıt")
    )
    st.altair_chart(cubuk(gunler, "Gün:N", "Kayıt:Q", renk=MURDUM, sira=GUNLER), width="stretch")
with sag:
    st.subheader("En çok izlenen 10 dizi")
    ilk10 = (
        f.loc[f["tur"] == "Dizi", "isim"].value_counts().head(10)
        .rename_axis("Dizi").reset_index(name="Kayıt")
    )
    st.dataframe(ilk10, hide_index=True, width="stretch")

# ---------- 6. Bir diziye yakından bak ----------
st.subheader("Bir diziye yakından bak")
diziler = f.loc[f["tur"] == "Dizi", "isim"].value_counts().index.tolist()
if diziler:
    secilen = st.selectbox("Dizi seç", diziler)
    d = f[f["isim"] == secilen]
    d_aylik = d.groupby(d["tarih"].dt.to_period("M")).size().rename("Kayıt").reset_index()
    d_aylik["Ay"] = d_aylik["tarih"].dt.to_timestamp()
    st.write(
        f"**{secilen}**: {len(d)} kayıt, ilk izleme {d['tarih'].min():%d.%m.%Y}, "
        f"son izleme {d['tarih'].max():%d.%m.%Y}."
    )
    st.altair_chart(cubuk(d_aylik, "yearmonth(Ay):T", "Kayıt:Q", renk=SEFTALI, x_baslik="Ay"), width="stretch")
else:
    st.write("Seçili filtrelerde dizi yok.")
