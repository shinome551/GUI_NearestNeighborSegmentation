# GUI_NearestNeighborSegmentation
<div align="center">
    <img src="https://raw.githubusercontent.com/wiki/shinome551/GUI_NearestNeighborSegmentation/images/usage.gif">
</div>

最近傍識別による領域分割のGUIアプリケーションです。  
tkinterとNumpy、Pillow、Cythonで動きます。

## 更新情報（05/09）
- 領域分割を特徴マップを介して行うように変更しました。  
モデルの詳細はpipeline.pyに記述しています。モデルを書き換える場合、出力は入力画像と解像度・チャネル数を一致させ、sigmoid関数などで値を0から1の範囲に収まるようにしてください。
- Trainボタンを追加しました。  
各クラスの事例を登録後、Trainボタンを押すことでモデルの学習が行われます。登録する事例の数が増えると一回の学習にかかる時間も増えます。

## 実行環境
```
Python  3.9.12
numpy   1.22.3
Pillow  8.4.0
Cython  0.29.28
```
Windowsで実行する場合はC++のコンパイラ（MinGWなど）が必要です。
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
# GUI上で読み込む画像を指定する場合
python main.py
# 画像のパスを引数として与える場合（デバッグ用）
python main.py --img_path [img_path]
```

## 操作とボタンの説明
画面上をドラッグ&ドロップすると矩形が描画され、矩形内部の画素が指定されたラベル（前景/背景）の事例として記録されます。  
記録後は自動的に領域分割が行われ、記録された事例をもとに画像上の画素が分類されます。生成された領域マスクは画像上に重ねて描画されます。  
領域分割後も引き続き事例を追加し、領域分割を再実行できます。描画された領域マスクを参考に調整していきましょう。  

- Visualize/Hide Maskボタン（トグルボタン）  
「Visualize Mask」ボタンを押すと領域マスクが画像上に重ねて描画されます。  
「Hide Mask」ボタンを押すと領域マスクが除去され、画像だけが描画されます（事例は記録されたままです）。

- Resetボタン  
記録された事例が初期化され、領域マスクが描画されていれば除去されます。  
また、指定するラベルの状態が前景に初期化されます。

- Background/Foregroundボタン（ラジオボタン）  
各ボタンをクリックすることで、事例を記録する際に指定するラベルを切り替えられます。  
初期状態は「Foreground」です。

- Saveボタン  
領域マスクが描画された画像を保存します。

- Loadボタン  
指定された画像を読み込みます。既存の領域マスクや登録された事例はリセットされます。

- Trainボタン  
登録された事例を用いてモデルの学習（二値分類）を行います。学習後は自動的に領域分割が更新されます。

## 注意
- 領域分割は前景事例と背景事例の両方を記録しなければ実行されません。適宜ラジオボタンでラベルを切り替えて矩形選択を行ってください。  
- 異なる解像度の入力画像を扱うため、現在は各事例を個別にforループで読み出しています。登録される事例の数が増えると一度の学習に時間がかかるため、記憶される事例の数を20に制限しています。
- モデルの詳細はpipeline.pyに記述しています（Encoderクラス）。モデルを書き換える場合、出力は入力画像と解像度・チャネル数を一致させ、sigmoid関数などで値を0から1の範囲に収まるようにしてください。
- 学習対象は特徴変換器（model）と分類器（classifier）に分割されています。分類器のアーキテクチャや学習の手続き全体を変更することも考えてみてください。
