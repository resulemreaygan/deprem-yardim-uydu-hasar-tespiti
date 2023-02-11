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

config.json dosyasındaki parametreleri belirledikten sonra aşağodaki komutu çalıştırabilirsiniz.

`python main.py`

## Katkı

Katkı yapmak isterseniz lütfen önce neyi değiştirmek istediğiniz ile ilgili bir issue açın.

## Lisans
[Apache 2.0](http://www.apache.org/licenses/)