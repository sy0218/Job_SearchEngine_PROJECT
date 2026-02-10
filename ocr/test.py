import easyocr, os, warnings
from PIL import Image
import numpy as np

os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"
warnings.filterwarnings("ignore")

reader = easyocr.Reader(['ko','en'], gpu=False)
#image_path = "/nfs/img/2c/91/2c914a6bef974f2e2046bef766d6a38872231fe1be0411148021dd804537eb5f"
image_path = "/nfs/img/cb/07/cb0763b304942c6c4508442258c4eb30789fbdd19e4057ec8461b4df9c160a20"
#with Image.open(image_path) as img:
#    print(f"Original Size: {img.size}") # 가로, 세로 출력
#    print(f"Image Mode: {img.mode}")

with Image.open(image_path) as img:
    img_np = np.array(img.convert('RGB'))

results = reader.readtext(img_np)
full_text = " ".join([text for _, text, _ in results])
print(full_text)
