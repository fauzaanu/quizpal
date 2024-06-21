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
Open-source bot by <a class="text-blue-600 underline dark:text-muted" href="https://fauzaanu.com/">@fauzaanu</a>.<br>
Uses Semantic Scholar API for research, OpenAI API for Q&A, and Telegram Bot API.<br>
70% cheaper than market. Free for usage, hosting, redistribution.<br>
Landing page uses Astrowind theme by <a class="text-blue-600 underline dark:text-muted" href="https://onwidget.com/">onWidget</a>.<br>
See also <a class="text-blue-600 underline dark:text-muted" href="https://lessonfuse.com/">LessonFuse</a>
</div>
`,
};


