import mvp
from users import client_data


def main():
  (
    question_list,
    audio_urls,
    main_dir
  ) = client_data.get()

  mvp.go(
      question_list, 
      audio_urls, 
      main_dir=main_dir,
      skip_transcribe=True,
      skip_map=True
    )

if __name__ == '__main__':
  main()

"""
client_data.get() return examples:

question_list : list[str] = [
  'What are some major pain points experienced by the user?',
  'What do users wish they could do with our product?',
  'What do people use our product for?',
]

audio_urls : dict[str,str] = {
  'interview_1.mp4': 'https://example.com/url-string-1-goes-here.mp4',
  'interview_2.avi': 'https://example.com/url-string-2-goes-here.avi',
  'interview_3.m4a': 'https://example.com/url-string-3-goes-here.m4a',
  ...
}

main_dir : str = 'demo/user_a/project_1'

"""

