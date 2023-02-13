# deprem-yardim-uydu-hasar-tespiti

Deprem yardım projesinin bir parçası olarak uydu görüntülerini TIFF formatı üzerinden belirlenen genişlik ve yükseklikte parçalara ayırma ile ilgili çalışmadır. 

Parçalara ayrılan görüntüler de etiketleme ve model eğitimi için kullanılacaktır.

## Installation

[pip](https://pip.pypa.io/en/stable/) veya [conda](https://docs.conda.io/en/latest/) paket yöneticisini kullanarak gerekli paketleri yükleyebilirsiniz.

```bash
pip install numpy~=1.19.5
pip install matplotlib~=3.1.2
pip install shapely~=2.0.1
pip install GDAL~=3.2
```
veya komutu direkt çalıştırarak kurulum yapabilirsiniz. `pip install -r requirements.txt`

GDAL kurulumunda sorun yaşarsanız iletişime geçebilirsiniz.

## Veriseti

Örnek veriseti paylaşılacaktır.

## Kullanım
### Colab:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/resulemreaygan/deprem-yardim-uydu-hasar-tespiti)
### Local:

config.json dosyasındaki parametreleri belirledikten sonra aşağodaki komutu çalıştırabilirsiniz.

`python main.py`

## Konfig Açıklaması

- `crop_size_x` = Çıktı raster'ın `genişliğini` temsil eder.
- `crop_size_y` = Çıktı raster'ın `yüksekliğini` temsil eder.
- `raster_path` = Kesilecek raster'ın `dosya yolunu` temsil eder.
- `output_dir` = Çıktı `dosya yolunu` temsil eder.
- `raster_format` = Çıktı raster'ın `formatını` temsil eder.
- `save_as_png` = Çıktı raster'ın yanına `png` formatında kopyasının üretilmesini temsil eder.

## Katkı

Katkı yapmak isterseniz lütfen önce neyi değiştirmek istediğiniz ile ilgili bir issue açın.

## Lisans
[Apache 2.0](http://www.apache.org/licenses/)
