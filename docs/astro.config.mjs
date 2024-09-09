import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'AIIDE',
			social: {
				github: 'https://github.com/Anilturaga/aiide',
			},
			sidebar: [
				{
					label: 'Introduction',
					slug: 'introduction/index',
				},
				{
					label: 'Tutorial',
					items: [
						// Each item here is one entry in the navigation menu.
						{ label: 'Task Management Assistant', slug: 'tutorial/example' },
					],
				},
				// {
				// 	label: 'Conceptual Guide',
				// 	items: [
				// 		// Each item here is one entry in the navigation menu.
				// 		{ label: 'AIIDE Chat', slug: 'concepts/aiide' },
				// 		{ label: 'Tools', slug: 'concepts/tool' },
				// 		{ label: 'Tool Helpers', slug: 'concepts/tool_def' },
				// 	],
				// },
				// {
				// 	label: 'How-To Guides',
				// 	items: [
				// 		// Each item here is one entry in the navigation menu.
				// 		{ label: 'ReAct Agent', slug: 'guides/react' },
				// 	],
				// },
				// {
				// 	label: 'Reference',
				// 	autogenerate: { directory: 'reference' },
				// },
			],
		}),
	],
});
