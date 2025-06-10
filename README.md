
# AI-Assistant-Scientific-Scout

The "AI Scientific Paper Scout" is a Python-based application designed to help users quickly discover and summarize recent research papers on any given topic.

It operates with a modular architecture:

1. Paper Search Server: Specializes in querying public academic databases (like arXiv) to find relevant papers.
2. PDF Summarize Server: Handles downloading specific PDF papers, extracting their text, and then generating a concise summary using a configured cloud-based Large Language Model (LLM) like OpenAI's GPT or Google's Gemini.
3. Agent Host (Frontend): This is the user-facing part (either a command-line interface or a Streamlit web app) that orchestrates the entire process. 

4. It takes the user's topic, sends requests to the search server, and then, for each found paper, requests a summary from the summarization server, finally presenting all the information to the user.



## Appendix

This project streamlines the research process by automating paper discovery and providing AI-powered summaries, saving users significant time and effort in staying updated with scientific literature.


![Logo](https://cdn-icons-png.flaticon.com/512/14232/14232225.png)


## API Reference

#### Get all items

```http
  openai_API_Key
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `api_key` | `string` | **Required**. Your API key |

#### Get item

```http
  google_API_key
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `string` | **Required**. YOUR API key |




## Demo

https://drive.google.com/file/d/1gFABpC38HKy8EkTk5pftzwK-540Ej9IP/view?usp=drivesdk


## Authors

- [@Anuj-shishodia](https://www.github.com/Anuj-shishodia)


## License

[MIT](https://choosealicense.com/licenses/mit/)

