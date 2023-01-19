import pandas as pd
import datetime as dt
import seaborn as sns
import matplotlib.pyplot as plot

pd.set_option("display.max_columns", None)
# pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', lambda x: '%.5f' % x)

# Online Retail II excelindeki 2010-2011 verisini okunması.

df_ = pd.read_excel("datasets/online_retail_II.xlsx", sheet_name="Year 2010-2011")
df = df_.copy()
df.head()

# Veri setinin betimsel istatistiklerini
quantile = [0.05,0.15,0.25,0.5,0.75,0.95,0.99]
df.describe(quantile).T

# Veri setinde eksik gözlem var mı?
df.isnull().any()
df.isnull().sum()


df.dropna(inplace=True)

# Eşsiz ürün sayısı
df["Description"].nunique()

# Hangi üründen kaçar tane var?
df["Description"].value_counts()

# En çok sipariş edilen 5 ürünü çoktan aza doğru sıralama
df.sort_values(by="Quantity",ascending=False)[["Description"]].head()

# Faturalardaki ‘C’ iptal edilen işlemleri göstermektedir. İptal edilen işlemlerin veri setinden çıkartılması.
df = df[~df["Invoice"].str.contains("C", na=False)]
df.describe(quantile).T

# Fatura başına elde edilen toplam kazancı ifade eden ‘TotalPrice’ adında bir değişken.
df = df[df["Price"] > 0]
df["TotalPrice"] = df["Quantity"] * df["Price"]
df.head()




# RFM metriklerinin hesaplanması
df["InvoiceDate"].max()

today_date = dt.datetime(2011, 12, 11)

rfm = df.groupby("Customer ID").agg({"InvoiceDate": lambda date: (today_date - date.max()).days,
                                     "Invoice": lambda Invoice: Invoice.nunique(),
                                     "TotalPrice": lambda totalPrice: totalPrice.sum() })

rfm.columns = ["recency", "frequency", "monetary"]


rfm = rfm[rfm["monetary"] > 0]

# RFM skorlarının oluşturulması ve tek bir değişkene çevrilmesi

rfm["recency_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1])
rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm["monetary_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5])

rfm["RFM_SCORE"] = rfm["recency_score"].astype(str) + rfm["frequency_score"].astype(str)


# RFM skorlarının segment olarak tanımlanması

seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)

# Aksiyon

rfm["segment"].value_counts()

ratio = pd.DataFrame({"segment": rfm["segment"].value_counts(),
                      "Ratio": 100 * rfm["segment"].value_counts() / len(rfm)})

sns.countplot(x=rfm["segment"], data=rfm)

# çoktan aza sıraladığımda ilk 3 segmentdeki müşterilerimin oranı
ratio.Ratio.head(3).sum()

# çoktan aza sıraladığımda önemli bulduğum segmentdeki müşterilerimin oranı
ratio["Ratio"][["champions","at_Risk","potential_loyalists","loyal_customers"]].sum()

# segmentlerin frekans değerlerini ve veri setine göre oranlarını incelediğimde
# müşterilerimin ½58 i hibernating,loyal_customers,champions segmentlerinden geliyor.

# hibernating segmentinden çok fazla müşterim var ama bu muşterilerin recency ve frekans değeri çok düşük olduğu için
# bu müşterilere özel bir ilginin geri dönüşü olacağını düşünmüyorum.

# önemli bulduğum segmentler champions,loyal_customers,at_Risk,potential_loyalists.

# champions ve loyal_customers segmentindeki müşterilerimin score ları yüksek olduğu için kendilerini değerli hissetirmek adına özel olduklarını
# söylerek indirim kuponları verebilirim

# at_Risk segmentindeki müşterilerimin sayısı fazla ve frequency değerleri de fena olmadığı için onları kaybetmek istemem
# bu yüzden ilgisini çekebilecek kampanyalarla iletişime geçerim.

# potential_loyalists segmentindeki müşterilerimin receny score ları yüksek olduğu için aldıkları
# hizmetleri inceleyerek cross-selling yaparak tavsiyelerde bulunurum.

##################################################################################

# "Loyal Customers" sınıfına ait customer ID'leri seçerek excel çıktısını alınız.
new_df = pd.DataFrame()
new_df["loyal_customer_id"] = rfm[rfm["segment"] == "loyal_customers"].index

new_df.to_excel("loyal_customers.xlsx")