| model               | comparison          |   n |   diff F1 (points) |      p |   p_holm |
|:--------------------|:--------------------|----:|-------------------:|-------:|---------:|
| qwen2.5:7b-instruct | C vs react_agent    | 126 |               -0.3 | 0.4397 |   0.4397 |
| qwen2.5:7b-instruct | C vs graph_verifier | 126 |                6.7 | 0.0005 |   0.0015 |
| qwen2.5:7b-instruct | C vs naive          | 126 |                2.6 | 0.212  |   0.424  |
| llama3.1:8b         | C vs react_agent    | 126 |               -1.3 | 0.0578 |   0.1156 |
| llama3.1:8b         | C vs graph_verifier | 126 |                2   | 0.2649 |   0.2649 |
| llama3.1:8b         | C vs naive          | 126 |               10.9 | 0.0003 |   0.0009 |