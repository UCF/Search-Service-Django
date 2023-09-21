export interface Image {
    block_level: number;
    city?: string;
    country?: string;
    description?: string;
    downloadable: boolean;
    duration?: number;
    ext?: string;
    featured_organization_name?: string;
    file_size: number;
    filename: string;
    grid_url?: string;
    guid: string;
    has_document_url: boolean;
    has_pdf_url: boolean;
    has_people?: string[];
    has_transcript: boolean;
    headline?: string;
    height?: number;
    id: number;
    mime_type?: string;
    permalink_url?: string;
    preview_image_url?: string;
    preview_type?: string;
    small_url?: string;
    submitted: boolean;
    taggable: boolean;
    tags: ImageTag[];
    thumb_url?: string;
    type: string;
    width?: number;
}

export interface ImageTag {
    id: number;
    name?: string;
    tag_id?: number;
    sub_type?: string;
}