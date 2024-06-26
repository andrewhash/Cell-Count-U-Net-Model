# -*- coding: utf-8 -*-
"""Cell_Count.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1johWLGCLWhUBtfpiqOLPsSMT7iRhV33o
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import torch
import sklearn as sk
import sklearn.model_selection
import sklearn.linear_model
import cv2

from google.colab import drive
drive.mount('/content/drive')

!unzip "/content/drive/My Drive/counting-cells-in-microscopy-images-2024.zip" -d "/content/counting-cells-data"

df_labeled = np.load('/content/counting-cells-data/train_data.npz')
df_test = np.load('/content/counting-cells-data/test_images.npz')

X_labeled = df_labeled['X']
y_labeled = df_labeled['y']

print(df_test.files)

X_train, X_val, y_train, y_val = sk.model_selection.train_test_split(X_labeled, y_labeled, train_size=.8)

print(X_train.shape)
print(X_val.shape)
print(df_test['X'].shape)

plt.imshow(X_train[0], cmap='gray')
plt.title('X Image')
plt.show()

plt.imshow(y_train[0], cmap='gray')
plt.title('y Image')
plt.show()

class CellSegmentationDataset():
  def __init__(self,images, masks):
    self.images = images
    self.masks = masks

  def __len__(self):
    return len(self.images)

  def __getitem__(self, i):
    image = self.images[i] / 255.0
    image = torch.tensor(image, dtype=torch.float32)
    image = torch.reshape(image, (1,128, 128))
    target = self.masks[i]
    target = torch.tensor(target, dtype=torch.float32)
    return image, target

class CellSegmentationDatasetTest():
  def __init__(self,images):
    self.images = images

  def __len__(self):
    return len(self.images)

  def __getitem__(self, i):
    image = self.images[i] / 255.0
    image = torch.tensor(image, dtype=torch.float32)
    image = torch.reshape(image, (1, 128, 128))
    return image

train_dataset = CellSegmentationDataset(X_train, y_train)
val_dataset = CellSegmentationDataset(X_val, y_val)
test_dataset = CellSegmentationDatasetTest(df_test['X'])

train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=16, shuffle=True)
val_dataloader = torch.utils.data.DataLoader(val_dataset, batch_size=16, shuffle=True)
test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=16, shuffle=False)

x_batch, y_batch = next(iter(val_dataloader))

x_batch.shape

class UNet(torch.nn.Module):
  def __init__(self):
    super().__init__()
    self.conv1 = torch.nn.Conv2d(1, 64, kernel_size=3, padding='same')
    self.conv2 = torch.nn.Conv2d(64, 64, kernel_size=3, padding='same')
    self.pool1 = torch.nn.MaxPool2d(kernel_size = 2, stride = 2)

    self.conv3 = torch.nn.Conv2d(64, 128, kernel_size=3, padding='same')
    self.conv4 = torch.nn.Conv2d(128, 128, kernel_size=3, padding='same')
    self.pool2 = torch.nn.MaxPool2d(kernel_size = 2, stride = 2)

    self.conv5 = torch.nn.Conv2d(128, 256, kernel_size=3, padding='same')
    self.conv6 = torch.nn.Conv2d(256, 256, kernel_size=3, padding='same')
    self.pool3 = torch.nn.MaxPool2d(kernel_size = 2, stride = 2)

    self.conv7 = torch.nn.Conv2d(256, 512, kernel_size=3, padding='same')
    self.conv8 = torch.nn.Conv2d(512, 512, kernel_size=3, padding='same')
    self.pool4 = torch.nn.MaxPool2d(kernel_size=2, stride = 2)

    self.conv9 = torch.nn.Conv2d(512, 1024, kernel_size=3, padding='same')
    self.conv10 = torch.nn.Conv2d(1024, 1024, kernel_size=3, padding='same')
    self.Upsample = torch.nn.Upsample(scale_factor=2)
    #ConCat
    self.conv11 = torch.nn.Conv2d(1536, 512, kernel_size=3, padding='same')#1024 + 512 = 1536
    self.conv12 = torch.nn.Conv2d(512, 512, kernel_size=3, padding='same')
    self.conv13 = torch.nn.Conv2d(512, 512, kernel_size=3, padding='same')
    #self.Upsample = torch.nn.Upsample(scale_factor=2)
    #ConCat
    self.conv14 = torch.nn.Conv2d(768, 256, kernel_size=3, padding='same') #512 + 256 = 768
    self.conv15 = torch.nn.Conv2d(256, 256, kernel_size=3, padding='same')
    #self.Upsample = torch.nn.Upsample(scale_factor=2)
    #ConCat
    self.conv16 = torch.nn.Conv2d(384, 128, kernel_size=3, padding='same') #256 + 128 = 384
    self.conv17 = torch.nn.Conv2d(128, 128, kernel_size=3, padding='same')
    #self.Upsample = torch.nn.Upsample(scale_factor=2)
    #ConCat
    self.conv18 = torch.nn.Conv2d(128, 128, kernel_size=3, padding='same')
    self.conv19 = torch.nn.Conv2d(192, 64, kernel_size=3, padding='same') #128 + 64 = 192
    self.conv20 = torch.nn.Conv2d(64, 64, kernel_size=3, padding='same')
    self.conv21 = torch.nn.Conv2d(64, 1, kernel_size=1, padding='same')
    self.relu = torch.nn.ReLU()

  def forward(self, x):
    x = self.conv1(x)
    x = self.relu(x)
    x = self.conv2(x)
    x1 = self.relu(x)
    x = self.pool1(x1)

    x = self.conv3(x)
    x = self.relu(x)
    x = self.conv4(x)
    x2 = self.relu(x)
    x = self.pool2(x)

    x = self.conv5(x)
    x = self.relu(x)
    x = self.conv6(x)
    x3 = self.relu(x)
    x = self.pool3(x)

    x = self.conv7(x)
    x = self.relu(x)
    x = self.conv8(x)
    x4 = self.relu(x)
    x = self.pool4(x)

    x = self.conv9(x)
    x = self.relu(x)
    x = self.conv10(x)
    x = self.relu(x)

    x = self.Upsample(x)

    x = torch.cat((x, x4), dim=1)

    x = self.conv11(x)
    x = self.relu(x)
    x = self.conv12(x)
    x = self.relu(x)
    x = self.conv13(x)
    x = self.relu(x)
    x = self.Upsample(x)

    x = torch.cat((x, x3), dim=1)

    x = self.conv14(x)
    x = self.relu(x)
    x = self.conv15(x)
    x = self.relu(x)
    x = self.Upsample(x)

    x = torch.cat((x, x2), dim=1)

    x = self.conv16(x)
    x = self.relu(x)
    x = self.conv17(x)

    x = self.relu(x)
    x = self.conv18(x)
    x = self.relu(x)
    x = self.Upsample(x)

    x = torch.cat((x, x1), dim=1)

    x = self.conv19(x)
    x = self.relu(x)
    x = self.conv20(x)
    x = self.relu(x)
    x = self.conv21(x)

    return x

model = UNet()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
loss_fun = torch.nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)

x_batch, y_batch = next(iter(train_dataloader))
x_batch = x_batch.to(device)
y_batch = y_batch.to(device)
outputs = model(x_batch)

outputs.shape

model

x_batch, y_batch = next(iter(train_dataloader))
x_batch = x_batch.to(device)
y_batch = y_batch.to(device)

y_pred = model(x_batch)
y_pred.shape

num_epochs = 30
ace_train_values = []
ace_val_values = []

for epoch in range(num_epochs):
  for x_batch, y_batch in train_dataloader:
    x_batch = x_batch.to(device)
    y_batch = y_batch.to(device)
    y_pred = model(x_batch)
    y_pred = torch.squeeze(y_pred, dim=1)
    loss = loss_fun(y_pred, y_batch)
    model.zero_grad()
    loss.backward()
    optimizer.step()

  ace_train = 0
  for x_batch, y_batch in train_dataloader:
      with torch.no_grad():
        x_batch = x_batch.to(device)
        y_batch = y_batch.to(device)
        y_pred = model(x_batch)
        y_pred = torch.squeeze(y_pred, dim=1)
        loss = loss_fun(y_pred, y_batch)
        ace_train = ace_train + loss * len(x_batch)

  ace_train = ace_train.item() / len(train_dataloader.dataset)
  ace_train_values.append(ace_train)

  ace_val = 0
  for x_batch, y_batch in val_dataloader:
      with torch.no_grad():
        x_batch = x_batch.to(device)
        y_batch = y_batch.to(device)
        y_pred = model(x_batch)
        y_pred = torch.squeeze(y_pred, dim=1)
        loss = loss_fun(y_pred, y_batch)
        ace_val = ace_val + loss * len(x_batch)
  ace_val = ace_val.item() / len(val_dataset)
  ace_val_values.append(ace_val)

  print(f'epoch is: {epoch}, ace_train is: {ace_train}, ace_val is: {ace_val}')

plt.figure()
plt.plot(range(num_epochs), ace_train_values, label='Training')
plt.plot(range(num_epochs), ace_val_values, label='Validation')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.show

sigmoid = torch.nn.Sigmoid()
counts = []

for x_batch in test_dataloader:
    x_batch = x_batch.to(device)
    outputs = model(x_batch)
    probabilities = sigmoid(outputs)
    labels = torch.round(probabilities)

    for i in range(len(labels)):
        img = labels[i].detach().cpu().numpy().squeeze().astype(np.uint8)
        info = cv2.connectedComponents(img)
        count = info[0] - 1
        counts.append(count)

print("Total counts collected:", len(counts))

submission_df = pd.DataFrame({
    'index': range(len(counts)),
    'count': counts})

len(submission_df)

submission_df.to_csv('/content/counting-cells-data/sample_submission.csv', index=False)
print(submission_df.head())
