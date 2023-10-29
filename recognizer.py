import os
import io
import sys
import cv2
import config
import easyocr
import numpy as np
from PIL import Image

# Stores all chunks of text within image

class TextRegion:
    def __init__(self, vertices, label, confidence):
        self.vertices = vertices
        self.label = label
        self.confidence = confidence

# Recognizer object and temp variables

reader = easyocr.Reader(config.DEFAULT_LANGUAGES)
font_color = config.FONT_COLOR_DEFAULT
textbox_color = config.TEXTBOX_LINE_COLOR_DEFAULT
language_selected = config.DEFAULT_LANGUAGES

# Setup new model

def prepare_reader_model(languages):
    global reader, language_selected
    reader = easyocr.Reader(languages) 
    language_selected = languages

# Setup textboxes

def setup_recognizer_color(color):
    global font_color, textbox_color
    font_color = color
    textbox_color = color

# Recognizer logic + boxing + labels

def drawLine(imageData, fromX, fromY, toX, toY):
    cv2.line(imageData, (fromX, fromY), (toX, toY), textbox_color, config.TEXTBOX_LINE_WIDTH)

def drawLabel(imageData, vertices, label):
    centerX = int((vertices[0][0] + vertices[2][0]) / 2)
    centerY = int((vertices[0][1] + vertices[2][1]) / 2)
    boxWidth = int(vertices[2][0] - vertices[0][0])
    if label != "":
        labelWidthToBoxWidthRatio = boxWidth / len(label)
        correction = labelWidthToBoxWidthRatio / 21
        labelWidth, labelHeight = cv2.getTextSize(label, cv2.FONT_HERSHEY_COMPLEX, config.FONT_SIZE * correction, config.FONT_THICKNESS)[0]
        labelCenterX = centerX - int(labelWidth / 2)
        labelCenterY = centerY + int(labelHeight / 2)
        cv2.putText(imageData, label, (labelCenterX, labelCenterY), cv2.FONT_HERSHEY_COMPLEX, config.FONT_SIZE * correction, font_color, config.FONT_THICKNESS)

def processTextBoxing(image_bytes, text_regions):
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    imageData = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
    for region in text_regions:
        drawLine(imageData, region.vertices[0][0], region.vertices[0][1], region.vertices[1][0], region.vertices[1][1])
        drawLine(imageData, region.vertices[1][0], region.vertices[1][1], region.vertices[2][0], region.vertices[2][1])
        drawLine(imageData, region.vertices[2][0], region.vertices[2][1], region.vertices[3][0], region.vertices[3][1])
        drawLine(imageData, region.vertices[3][0], region.vertices[3][1], region.vertices[0][0], region.vertices[0][1])
        drawLabel(imageData, region.vertices, region.label)
    image = Image.fromarray(imageData)
    return image

def mappedToTextRegions(results):
    text_regions = []
    for result in results:
        a, b, c, d = result[0]
        leftTop = (int(a[0]), int(a[1]))
        rightTop = (int(b[0]), int(b[1]))
        rightBottom = (int(c[0]), int(c[1]))
        leftBottom = (int(d[0]), int(d[1]))
        label = result[1]
        confidence = result[2]
        text_region = TextRegion([leftTop, rightTop, rightBottom, leftBottom], label, confidence)
        text_regions.append(text_region)
    return text_regions

def proccess_image(image_data):
    result = reader.readtext(image_data)
    text_regions = mappedToTextRegions(result)
    imageTextLabels = []
    for region in text_regions:
        imageTextLabels.append(region.label)
    message = " ".join(imageTextLabels)
    image_data_boxed = processTextBoxing(image_data, text_regions) 
    return (message, image_data_boxed)
    
