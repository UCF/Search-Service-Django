export interface ProgramAPIResults {
    count: number;
    next?: string;
    previous?: string;
    results: Program[];
}

export interface ProgramDescription {
    id: number;
    description_type: {
        id: number;
        name: string;
    };
    description: string;
    primary: boolean;
    program: number;
    update_url: string;
}

export interface ProgramProfile {
    profile_type: {
        id: number;
        name: string;
        root_url: string;
    };
    url: string;
    primary: boolean;
    program: number;
    update_url: string;
}

export interface College {
    name: string;
    full_name: string;
    short_name: string;
    college_url?: string;
    profile_url?: string;
    update_url?: string;
}

export interface Department {
    name: string;
    full_name: string;
    department_url?: string;
    school: boolean;
    update_url?: string;
}

export interface Term {
    full_name: string;
    semester: string;
    semester_index: number;
    year: number;
}

export interface ProgramSimple {
    id: number;
    name: string;
    online: boolean;
    url: string;
}

export interface Program {
    id: number;
    name: string;
    descriptions: ProgramDescription[];
    credit_hours: number;
    online: boolean;
    has_online: boolean;
    profiles: ProgramProfile[];
    primary_profile_url: string;
    plan_code: string;
    subplan_code?: string;
    catalog_url?: string;
    colleges: College[];
    departments: Department[];
    level: string;
    career: string;
    degree: string;
    parent_program?: number;
    subplans: ProgramSimple[];
    resident_tuition?: number;
    nonresident_tuition?: number;
    tuition_type?: string;
    outcomes?: string;
    projection_totals?: string;
    careers?: string;
    application_deadlines?: string;
    graduate_slate_id?: string;
    valid: boolean;
    has_locations: boolean;
    active: boolean;
    start_term: Term;
    excerpt?: string;
    area_of_interest?: string;
}