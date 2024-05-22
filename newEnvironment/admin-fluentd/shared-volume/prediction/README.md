# MLP_11agosto.keras
It's the model od neural network computed in .keras extension.
<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="font-weight: bold">Model: "sequential"</span>
</pre>
<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃<span style="font-weight: bold"> Layer (type)                    </span>┃<span style="font-weight: bold"> Output Shape           </span>┃<span style="font-weight: bold">       Param # </span>┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ dense (<span style="color: #0087ff; text-decoration-color: #0087ff">Dense</span>)                   │ (<span style="color: #00d7ff; text-decoration-color: #00d7ff">None</span>, <span style="color: #00af00; text-decoration-color: #00af00">6</span>)              │            <span style="color: #00af00; text-decoration-color: #00af00">66</span> │
├─────────────────────────────────┼────────────────────────┼───────────────┤
│ dense_1 (<span style="color: #0087ff; text-decoration-color: #0087ff">Dense</span>)                 │ (<span style="color: #00d7ff; text-decoration-color: #00d7ff">None</span>, <span style="color: #00af00; text-decoration-color: #00af00">6</span>)              │            <span style="color: #00af00; text-decoration-color: #00af00">42</span> │
├─────────────────────────────────┼────────────────────────┼───────────────┤
│ dense_2 (<span style="color: #0087ff; text-decoration-color: #0087ff">Dense</span>)                 │ (<span style="color: #00d7ff; text-decoration-color: #00d7ff">None</span>, <span style="color: #00af00; text-decoration-color: #00af00">1</span>)              │             <span style="color: #00af00; text-decoration-color: #00af00">7</span> │
└─────────────────────────────────┴────────────────────────┴───────────────┘
</pre>


# std_scaler.bin
It's the standard scaler based on the training set used for the model. It is used to scale the data to be analysed so that they fit in the same range of the training set. 
The aim of this operation is to maintain the numerical stability of the learning process and ensure that weights and biases are updated appropriately during backpropagation.

# 1prediction.py
It's the script that live predict each entry received by fluentd. 

# temp.txt
It's where the live prediction results of each entry are saved.

# intervalModelUser.py
It's a script that analyses a time interval of entries, given the name of the logfile as argument.

# manualModelUser.py
It's a script that analyses an entry per time given as argument

# trialmodeluser.py
It's the first trial using the model and the scaler
