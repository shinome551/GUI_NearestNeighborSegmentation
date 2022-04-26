# GUI_NearestNeighborSegmentation
<div align="center">
    <img src="https://raw.githubusercontent.com/wiki/shinome551/GUI_NearestNeighborSegmentation/images/usage.gif">
</div>

最近傍識別による領域分割のGUIアプリケーションです。  
tkinterとNumpy、Pillow、Cythonで動きます。

## 実行環境
```
Python  3.9.12
numpy   1.22.3
Pillow  8.4.0
Cython  0.29.21
```
- tkinterが使えない場合  
```
# for ubuntu
sudo apt-get install python3-tk
sudo apt-get install tk-dev
```
```
# for mac
brew install python-tk@3.9
```

## 利用方法
```
git clone https://github.com/shinome551/GUI_NearestNeighborSegmentation.git
cd GUI_NearestNeighborSegmentation
```
```
# .pyx compile
cd cy
python setup.py build_ext --inplace
cd ../
```
```
# main.pyの引数として画像のパスを与える
# python main.py --img_path [img_path]
# サンプル画像での例
python main.py --img_path img/fox.jpg
```

## 操作とボタンの説明
画面上をドラッグ&ドロップすると矩形が描画され、矩形内部の画素が指定されたラベル（前景/背景）の事例として記録されます。  
記録後は自動的に領域分割が行われ、記録された事例をもとに画像上の画素が分類されます。生成された領域マスクは画像上に重ねて描画されます。  
領域分割後も引き続き事例を追加し、領域分割を再実行できます。描画された領域マスクを参考に調整していきましょう。  

- Visualize/Hide Maskボタン（トグルボタン）  
「Visualize Mask」ボタンを押すと領域マスクが画像上に重ねて描画されます。  
「Hide Mask」ボタンを押すと領域マスクが除去され、画像だけが描画されます（事例は記録されたままです）。

- Resetボタン  
記録された事例が初期化され、領域マスクが描画されていれば除去されます。また、指定するラベルの状態が前景に初期化されます。

- Background/Foregroundボタン（ラジオボタン）  
各ボタンをクリックすることで、事例を記録する際に指定するラベルを切り替えられます。初期状態は「Foreground」です。

## 注意
- 領域分割は前景事例と背景事例の両方を記録しなければうまく機能しません。適宜ラジオボタンを使ってラベルを切り替えてください。  
