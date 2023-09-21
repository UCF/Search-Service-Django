export interface EventAPIResponse {
    count: number;
    next: string;
    previous: string;
    results: Array<EventResult>;
}

export interface EventResult {
    object_type: string;
    object_id: string;
    title: string;
    description: string;
    url: string;
    details: string;
}

export interface Calendar {
    id: number;
    title: string;
    slug: string;
    url: string;
}

export interface EventDetail {
    event_id: string;
    eventinstance_id: string;
    calendar: Calendar;
    id: string;
    title: string;
    subtitle?: string;
    description?: string;
    location?: string;
    virtual_url?: string;
    registration_link?: string;
    registration_info?: string;
    starts: string;
    ends: string;
    ongoing: string;
    category: string;
    tags: string[];
    contact_name?: string;
    contact_phone?: string;
    contact_email?: string;
    url: string;
}