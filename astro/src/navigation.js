import {getBlogPermalink, getPermalink} from './utils/permalinks';

export const headerData = {
  links: [
    {
      text: 'Blog',
      href: getBlogPermalink(),
    },
    {
      text: 'Terms',
      href: getPermalink('/terms'),
    },
    {
      text: 'Privacy',
      href: getPermalink('/privacy'),
    },
  ],
  actions: [{text: '/Start', href: 'https://t.me/quizpalbot', target: '_blank'}],
};

export const footerData = {
  footNote: `
<div>
@QuizpalBot is an Opensource Bot Made by <a class="text-blue-600 underline dark:text-muted" href="https://onwidget.com/">@fauzaanu</a>.<br>
@QuizpalBot uses Semantic Scholar API to fetch the latest research papers, OpenAI API to generate questions and answers, and Telegram Bot API as a means to interact with our users.<br>
@Quizpalbot has its pricing model set as a usage based model and is 70% cheaper than the market average ($60 per year).<br>
Users who dont want to pay can use, host, redistribute, whitelabel and resell @Quizpalbot on their own hardware for free without limitations.<br>
Astrowind theme used here as a <a class="text-blue-600 underline dark:text-muted" href="https://astro.build/">Astro</a> landing page was made by <a class="text-blue-600 underline dark:text-muted" href="https://onwidget.com/">onWidget</a>
<br>
Also checkout my other product, - <a class="text-blue-600 underline dark:text-muted" href="https://lessonfuse.com/">
LessonFuse</a> - A tool for teachers to create lessonplans in a really fast way while also staying inline with the curriculum. We directly use the syllabus within the platform to achieve this quality increase and there is no other service that takes our approach as of now.
`,
};
