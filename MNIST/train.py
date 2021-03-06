import time
import torch
import pandas as pd
import matplotlib.pyplot as plt
from torchvision import transforms
from torchvision.datasets import MNIST
from torch.utils.data import DataLoader
from collections import defaultdict
from model import *
from torchvision.datasets import MNIST,CIFAR10
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import numpy as np
mnist_transform = transforms.Compose([
        transforms.ToTensor(),
])

PLOT = False
kwargs = {} 
def get_same_index(target, label):
    label_indices = []
    for i in range(len(target)):
        if target[i] == label:
            label_indices.append(i)
    return label_indices
cuda = True
DEVICE = torch.device("cuda" if cuda else "cpu")
dataset_path = '~/datasets'
batch_size = 128

train_dataset_raw = MNIST(dataset_path, transform=mnist_transform, train=True, download=True)
test_dataset_raw  = MNIST(dataset_path, transform=mnist_transform, train=False, download=True)
print(len(test_dataset_raw))
# train_dataset_raw = train_dataset_raw[:30000]
print(len(train_dataset_raw))
train_loader = DataLoader(dataset=train_dataset_raw, batch_size=batch_size, shuffle=True, **kwargs)
test_loader1  = DataLoader(dataset=test_dataset_raw,  batch_size=batch_size, shuffle=True,  **kwargs)
label_class = 1 # ones

def loss_fn(recon_x, x, mean, log_var):
    BCE = torch.nn.functional.binary_cross_entropy(
        recon_x.view(-1, 28*28*1), x.view(-1, 28*28*1), reduction='sum')
    KLD = -0.5 * torch.sum(1 + log_var - mean.pow(2) - log_var.exp())

    return (BCE + KLD) / x.size(0)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Get indices of label_class
# train_indices = get_same_index(train_dataset_raw, label_class)

# one_set = torch.utils.data.Subset(train_dataset_raw, train_indices)
seed = 1
torch.manual_seed(seed)
if torch.cuda.is_available():
    torch.cuda.manual_seed(seed)


ts = time.time()

# dataset = MNIST(
#     root='data', train=True, transform=transforms.ToTensor(),
#     download=True)
data_loader = DataLoader(
    dataset=test_dataset_raw, batch_size=batch_size, shuffle=True)

# data_loader = test_loader
epochs=50
learning_rate=0.001
latent_size=128
print_every=100
fig_root='figs'
device = 'cuda'
n_labels = 10

logs = defaultdict(list)
for clas in range(10) :
    conditional = False
    print("Training for class ", str(clas))
    model = VAE_conv(
            label='MNIST',
            image_size=28,
            channel_num=1,
            kernel_num=128,
            z_size=128,
            conditional=False,
            n_labels=10
        ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    train_indices = get_same_index(train_dataset_raw.targets, clas)
    bird_set = torch.utils.data.Subset(train_dataset_raw, train_indices)
    train_loader_dash = torch.utils.data.DataLoader(dataset=bird_set, shuffle=True,
                                           batch_size=batch_size, drop_last=True)
    # plt.figure(figsize=(5, 10))
    # plt.show(block=False)
    for epoch in range(epochs):
        tracker_epoch = defaultdict(lambda: defaultdict(dict))
        for iteration, (x, y) in enumerate(train_loader_dash):
            x, y = x.to(device), y.to(device)
            # print(x.shape)
            if conditional:
                recon_x, mean, log_var, z = model(x, y)
            else:
                recon_x, mean, log_var, z = model(x)

            for i, yi in enumerate(y):
                id = len(tracker_epoch)
                tracker_epoch[id]['x'] = z[i, 0].item()
                tracker_epoch[id]['y'] = z[i, 1].item()
                tracker_epoch[id]['label'] = yi.item()
            # print(recon_x.shape)
            loss = loss_fn(recon_x, x, mean, log_var)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            logs['loss'].append(loss.item())

            if iteration % 600 == 0 or iteration == len(data_loader)-1:
                print("Epoch {:02d}/{:02d} Batch {:04d}/{:d}, Loss {:9.4f}".format(
                    epoch, epochs, iteration, len(data_loader)-1, loss.item()))
                torch.save(model.state_dict(), 'curr_t'+str(clas)+'.pt')
                if conditional:
                    c = torch.arange(0, n_labels).long().unsqueeze(1).to(device)
                    z = torch.randn([c.size(0), 128]).to(device)
                    x = model.inference(z, c=c)
                else:
                    z_dash = torch.randn([10, 128]).to(device)
                    z_dash[4:8,:] = z[:4,:]
                    x_dash = model.inference(z_dash)
                    x_dash[:4,:,:,:] = x[:4,:,:,:]

                # plt.figure()
                # if 
                if PLOT : 
                    plt.figure(figsize=(5, 10))
                    for p in range(10):
                        plt.subplot(5, 2, p+1)
                        if conditional:
                            plt.text(
                                0, 0, "c={:d}".format(c[p].item()), color='black',
                                backgroundcolor='white', fontsize=8)
                        plt.imshow(x_dash[p].view(1,28,28).permute(1,2,0)[:,:,0].cpu().data.numpy())
                        plt.axis('off')
                    plt.show()
                # plt.clf()
                # plt.close('all')

        df = pd.DataFrame.from_dict(tracker_epoch, orient='index')
        # g = sns.lmplot(
        #     x='x', y='y', hue='label', data=df.groupby('label').head(100),
        #     fit_reg=False, legend=True)

