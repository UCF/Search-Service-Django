export interface NewsItem {
    id: number;
    date: Date;
    date_gmt: Date;
    modified: Date;
    modified_gmt: Date;
    slug: string;
    status: string;
    link: string;
    title: {
        rendered: string;
    };
    content: {
        rendered: string;
        protected: boolean;
    };
    excerpt: {
        rendered: string;
        protected: boolean;
    };
    author: number;
    categories: number[];
    tags: number[];
    thumbnail?: string;
    primary_category?: number;
    primary_tag?: number;
    author_byline?: string;
}