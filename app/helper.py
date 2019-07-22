def ngitung_author(jumlah):
  tmp = []
  for tahun in tqdm(range(awal, akhir)):
    cnt = 0
    article_id = df[(df.year == tahun)].c_article_id
    for id in set(article_id):
      if len([n for n in article_id if n == id]) == jumlah or (len([n for n in article_id if n == id]) >= jumlah and jumlah == 6):
        cnt += 1
    tmp.append(cnt)
  return tmp