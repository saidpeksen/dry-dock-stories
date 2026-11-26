# Aktarım denemesi (U00, kuru havuza alma)

Yayınlanmayan deneme videosunun ana kopyası, baytları değişmeden parçalara bölünmüş hâlde. Yalnız aktarım yolunu
ölçmek içindir; deneme bitince bu dal silinir.

- `video-parcalar.json`: parçaların adı, bayt sayısı ve sha256 değeri; birleşmiş dosyanın `toplam_bayt` ve `sha256` değeri.
- `video-parca-NN.bin`: parçalar. Ad sırasıyla uç uca eklenince `video.mp4` olur (yeniden kodlama yok):
  `cat video-parca-*.bin > video.mp4`
