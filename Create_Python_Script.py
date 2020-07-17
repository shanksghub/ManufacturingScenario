#!/usr/bin/env python
# coding: utf-8

# # Step1: Create the Python Script
# 
# In the cell below, you will need to complete the Python script and run the cell to generate the file using the magic `%%writefile` command. Your main task is to complete the following methods for the `PersonDetect` class:
# * `load_model`
# * `predict`
# * `draw_outputs`
# * `preprocess_outputs`
# * `preprocess_inputs`
# 
# For your reference, here are all the arguments used for the argument parser in the command line:
# * `--model`:  The file path of the pre-trained IR model, which has been pre-processed using the model optimizer. There is automated support built in this argument to support both FP32 and FP16 models targeting different hardware.
# * `--device`: The type of hardware you want to load the model on (CPU, GPU, MYRIAD, HETERO:FPGA,CPU)
# * `--video`: The file path of the input video.
# * `--output_path`: The location where the output stats and video file with inference needs to be stored (results/[device]).
# * `--max_people`: The max number of people in queue before directing a person to another queue.
# * `--threshold`: The probability threshold value for the person detection. Optional arg; default value is 0.60.

# In[ ]:





# In[1]:


get_ipython().run_cell_magic('writefile', 'person_detect.py', '\nimport numpy as np\nimport time\nfrom openvino.inference_engine import IECore\nimport os\nimport cv2\nimport argparse\nimport sys\n\n\nclass Queue:\n    \'\'\'\n    Class for dealing with queues\n    \'\'\'\n    def __init__(self):\n        self.queues=[]\n\n    def add_queue(self, points):\n        self.queues.append(points)\n\n    def get_queues(self, image):\n        for q in self.queues:\n            x_min, y_min, x_max, y_max=q\n            frame=image[y_min:y_max, x_min:x_max]\n            yield frame\n    \n    def check_coords(self, coords):\n        d={k+1:0 for k in range(len(self.queues))}\n        for coord in coords:\n            for i, q in enumerate(self.queues):\n                if coord[0]>q[0] and coord[2]<q[2]:\n                    d[i+1]+=1\n        return d\n\n\nclass PersonDetect:\n    \'\'\'\n    Class for the Person Detection Model.\n    \'\'\'\n\n    def __init__(self, model_name, device, threshold=0.60):\n        self.model_weights=model_name+\'.bin\'\n        self.model_structure=model_name+\'.xml\'\n        self.device=device\n        self.threshold=threshold\n\n        try:\n            self.core = IECore()\n            self.model=core.read_network(model=model_structure, weights=model_weights)\n        except Exception as e:\n            raise ValueError("Could not Initialise the network. Have you enterred the correct model path?")\n\n        self.input_name=next(iter(self.model.inputs))\n        self.input_shape=self.model.inputs[self.input_name].shape\n        self.output_name=next(iter(self.model.outputs))\n        self.output_shape=self.model.outputs[self.output_name].shape\n\n    def load_model(self):\n        self.net = self.core.load_network(network=self.model, device_name=self.device, num_requests=1)\n\n        \n    def predict(self, image):\n        net_input = self.preprocess_input(image)\n        infer_request_handle = self.network.start_async(request_id=0, inputs=net_input)\n        if infer_request_handle.wait() == 0:\n            net_output = infer_request_handle.outputs[self.output_name]\n            boxes = self.preprocess_outputs(net_output)\n            return self.draw_outputs(boxes, image)\n    \n    def draw_outputs(self, coords, image):\n    \n        \n        current_count = 0\n        coords = []\n        for obj in result[0][0]:\n        # Draw bounding box for object when it\'s probability is more than\n        #  the specified threshold\n            if obj[2] > prob_threshold:\n                xmin = int(obj[3] * initial_w)\n                ymin = int(obj[4] * initial_h)\n                xmax = int(obj[5] * initial_w)\n                ymax = int(obj[6] * initial_h)\n                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 5), 1)\n                current_count = current_count + 1\n                det.append(obj)\n            \n            return frame, current_count\n\n        \n    def preprocess_outputs(self, outputs):\n        d = []\n        for coord in coords:\n            for i, q in enumerate(self.queues):\n                if coord[0]>q[0] and coord[2]<q[2]:\n                    d[i+1]+=1\n        return d\n\n    def preprocess_input(self, image):\n    \n        image = cv2.resize(image, (self.input_shape[3], self.input_shape[2]))\n        image = image.transpose((2, 0, 1))\n        image = image.reshape(1, 3, self.input_shape[2], self.input_shape[3])\n        return image\n    \n\ndef main(args):\n    model=args.model\n    device=args.device\n    video_file=args.video\n    max_people=args.max_people\n    threshold=args.threshold\n    output_path=args.output_path\n\n    start_model_load_time=time.time()\n    pd= PersonDetect(model, device, threshold)\n    pd.load_model()\n    total_model_load_time = time.time() - start_model_load_time\n\n    queue=Queue()\n    \n    try:\n        queue_param=np.load(args.queue_param)\n        for q in queue_param:\n            queue.add_queue(q)\n    except:\n        print("error loading queue param file")\n\n    try:\n        cap=cv2.VideoCapture(video_file)\n    except FileNotFoundError:\n        print("Cannot locate video file: "+ video_file)\n    except Exception as e:\n        print("Something else went wrong with the video file: ", e)\n    \n    initial_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))\n    initial_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))\n    video_len = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))\n    fps = int(cap.get(cv2.CAP_PROP_FPS))\n    out_video = cv2.VideoWriter(os.path.join(output_path, \'output_video.mp4\'), cv2.VideoWriter_fourcc(*\'avc1\'), fps, (initial_w, initial_h), True)\n    \n    counter=0\n    start_inference_time=time.time()\n\n    try:\n        while cap.isOpened():\n            ret, frame=cap.read()\n            if not ret:\n                break\n            counter+=1\n            \n            coords, image= pd.predict(frame)\n            num_people= queue.check_coords(coords)\n            print(f"Total People in frame = {len(coords)}")\n            print(f"Number of people in queue = {num_people}")\n            out_text=""\n            y_pixel=25\n            \n            for k, v in num_people.items():\n                out_text += f"No. of People in Queue {k} is {v} "\n                if v >= int(max_people):\n                    out_text += f" Queue full; Please move to next Queue "\n                cv2.putText(image, out_text, (15, y_pixel), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)\n                out_text=""\n                y_pixel+=40\n            out_video.write(image)\n            \n        total_time=time.time()-start_inference_time\n        total_inference_time=round(total_time, 1)\n        fps=counter/total_inference_time\n\n        with open(os.path.join(output_path, \'stats.txt\'), \'w\') as f:\n            f.write(str(total_inference_time)+\'\\n\')\n            f.write(str(fps)+\'\\n\')\n            f.write(str(total_model_load_time)+\'\\n\')\n\n        cap.release()\n        cv2.destroyAllWindows()\n    except Exception as e:\n        print("Could not run Inference: ", e)\n\nif __name__==\'__main__\':\n    parser=argparse.ArgumentParser()\n    parser.add_argument(\'--model\', required=True)\n    parser.add_argument(\'--device\', default=\'CPU\')\n    parser.add_argument(\'--video\', default=None)\n    parser.add_argument(\'--queue_param\', default=None)\n    parser.add_argument(\'--output_path\', default=\'/results\')\n    parser.add_argument(\'--max_people\', default=2)\n    parser.add_argument(\'--threshold\', default=0.60)\n    \n    args=parser.parse_args()\n\n    main(args)')


# In[ ]:




