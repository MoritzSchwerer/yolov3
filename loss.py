#!/usr/bin/env python3

import torch
import torch.nn as nn

from iou import iou


class YoloLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.mse = nn.MSELoss()
        self.bce = nn.BCEWithLogitsLoss()
        self.entropy = nn.CrossEntropyLoss()
        self.sigmoid = nn.Sigmoid()


        # constants
        self.lambda_class = 1
        self.lambda_noobj = 1
        self.lambda_obj = 1
        self.lambda_box = 10

    def forward(self, predictions, target, anchors):
        obj = target[..., 0] == 1
        noobj = target[..., 0] == 0

        # no obj loss
        no_object_loss = self.bce(
            (predictions[..., 0:1][noobj], (target[..., 0:1][noobj]))
        )

        # obj loss
        anchors = anchors.respahe(1, 3, 1, 1, 2)
        box_preds = torch.cat([self.sigmoid(predictions[..., 1:3]),
                               torch.exp(predictions[..., 3:5 ]) * anchors], dim=-1)
        ious = iou(box_preds[obj], target[..., 1:5][obj]).detach()
        object_loss = self.bce((predictions[..., 0:1][obj]), (ious * target[..., 0:1]))

        # Box coordinate loss
        predictions[..., 1:3] = self.sigmoid(predictions[..., 1:3])
        target[..., 3:5] = torch.log(
            target[..., 3:5] / anchors + 1e-6
        )
        box_loss = self.mse(predictions[..., 1:5][obj], target[..., 1:5][obj])

        # class loss
        class_loss = self.entropy(
            (predictions[..., 5:][obj]), (target[..., 5][obj].long())
        )

        return (self.lambda_box * box_loss +
                self.lambda_obj * object_loss +
                self.lambda_noobj * no_object_loss +
                self.lambda_class * class_loss)
