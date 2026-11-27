# U00 v3, 1080p ana kopya (aktarım)

"How Ships Are Dry-Docked" videosunun 1920×1080 ana kopyası, baytları değişmeden parçalara bölünmüş hâlde.
YouTube'a yüklenecek dosya budur. Yükleme doğrulandıktan sonra bu dal silinir.

- `video-parcalar.json`: parçaların adı, bayt sayısı ve sha256 değeri; birleşmiş dosyanın `toplam_bayt` ve `sha256` değeri.
- `video-parca-NN.bin`: parçalar. Ad sırasıyla uç uca eklenince `video.mp4` olur (yeniden kodlama yok):
  `cat video-parca-*.bin > video.mp4`
