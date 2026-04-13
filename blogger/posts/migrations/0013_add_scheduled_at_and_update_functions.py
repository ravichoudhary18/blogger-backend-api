from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0012_alter_post_total_comments_alter_post_total_likes_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="scheduled_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Publication date and time for scheduled posts.",
                null=True,
            ),
        ),
        migrations.RunSQL(
            sql="""
            -- Update add_post function to include scheduled_at
            CREATE OR REPLACE FUNCTION add_post(
                p_title VARCHAR, 
                p_content TEXT, 
                p_author_id INT, 
                p_status VARCHAR,
                p_created_at TIMESTAMP WITH TIME ZONE,
                p_updated_at TIMESTAMP WITH TIME ZONE,
                p_thumbnail VARCHAR DEFAULT NULL,
                p_scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
            )
            RETURNS INT
            LANGUAGE plpgsql
            AS $$
            DECLARE
                new_id INT;
            BEGIN
                INSERT INTO posts_post (
                    title, content, author_id, status, 
                    created_by_id, updated_by_id, 
                    created_at, updated_at, thumbnail, scheduled_at
                )
                VALUES (
                    p_title, p_content, p_author_id, p_status, 
                    p_author_id, p_author_id, 
                    p_created_at, p_updated_at, p_thumbnail, p_scheduled_at
                )
                RETURNING id INTO new_id;
                
                RETURN new_id;
            END;
            $$;

            -- Update update_post procedure to include scheduled_at
            CREATE OR REPLACE PROCEDURE update_post(
                p_post_id INT, 
                p_title VARCHAR, 
                p_content TEXT, 
                p_status VARCHAR, 
                p_updated_by_id INT,
                p_updated_at TIMESTAMP WITH TIME ZONE,
                p_thumbnail VARCHAR DEFAULT NULL,
                p_scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                UPDATE posts_post
                SET title = p_title,
                    content = p_content,
                    status = p_status,
                    updated_by_id = p_updated_by_id,
                    updated_at = p_updated_at,
                    thumbnail = COALESCE(p_thumbnail, thumbnail),
                    scheduled_at = p_scheduled_at
                WHERE id = p_post_id;
            END;
            $$;

            -- Update get_post_by_id function to handle scheduled status
            CREATE OR REPLACE FUNCTION get_post_by_id(p_post_id INT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', p.id,
                    'title', p.title,
                    'content', p.content,
                    'status', p.status,
                    'author', p.author_id,
                    'author_username', u.username,
                    'thumbnail', p.thumbnail,
                    'likes_count', (SELECT COUNT(*) FROM interaction_like WHERE post_id = p.id),
                    'comments_count', (SELECT COUNT(*) FROM interaction_comment WHERE post_id = p.id),
                    'share_count', (SELECT COUNT(*) FROM interaction_share WHERE post_id = p.id),
                    'documents', (
                        SELECT COALESCE(json_agg(d), '[]'::json)
                        FROM (
                            SELECT id, file, description, uploaded_at
                            FROM posts_document
                            WHERE post_id = p.id
                        ) d
                    ),
                    'created_at', p.created_at,
                    'updated_at', p.updated_at,
                    'scheduled_at', p.scheduled_at
                ) INTO result
                FROM posts_post p
                JOIN auth_user u ON u.id = p.author_id
                WHERE p.id = p_post_id 
                  AND (p.status = 'public' OR (p.status = 'scheduled' AND p.scheduled_at <= NOW()));

                RETURN result;
            END;
            $$;

            -- Update get_posts function to handle scheduled status
            CREATE OR REPLACE FUNCTION get_posts(
                p_title VARCHAR DEFAULT NULL,
                p_author VARCHAR DEFAULT NULL,
                p_start_date DATE DEFAULT NULL,
                p_end_date DATE DEFAULT NULL,
                p_limit INT DEFAULT 10,
                p_offset INT DEFAULT 0
            )
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                total_count INT;
            BEGIN
                -- Get total count for pagination
                SELECT COUNT(*) INTO total_count
                FROM posts_post p
                JOIN auth_user u ON u.id = p.author_id
                WHERE (p.status = 'public' OR (p.status = 'scheduled' AND p.scheduled_at <= NOW()))
                  AND (p_title IS NULL OR p.title ILIKE '%' || p_title || '%')
                  AND (p_author IS NULL OR u.username ILIKE '%' || p_author || '%')
                  AND (p_start_date IS NULL OR p.created_at::date >= p_start_date)
                  AND (p_end_date IS NULL OR p.created_at::date <= p_end_date);

                -- Get paginated results with counts
                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(post_row)
                         FROM (
                            SELECT
                                p.id,
                                p.title,
                                p.content,
                                p.status,
                                p.author_id AS author,
                                u.username AS author_username,
                                p.thumbnail,
                                (SELECT COUNT(*) FROM interaction_like WHERE post_id = p.id) AS likes_count,
                                (SELECT COUNT(*) FROM interaction_comment WHERE post_id = p.id) AS comments_count,
                                (SELECT COUNT(*) FROM interaction_share WHERE post_id = p.id) AS share_count,
                                p.created_at,
                                p.updated_at,
                                p.scheduled_at
                            FROM posts_post p
                            JOIN auth_user u ON u.id = p.author_id
                            WHERE (p.status = 'public' OR (p.status = 'scheduled' AND p.scheduled_at <= NOW()))
                              AND (p_title IS NULL OR p.title ILIKE '%' || p_title || '%')
                              AND (p_author IS NULL OR u.username ILIKE '%' || p_author || '%')
                              AND (p_start_date IS NULL OR p.created_at::date >= p_start_date)
                              AND (p_end_date IS NULL OR p.created_at::date <= p_end_date)
                            ORDER BY p.created_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) post_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """,
            reverse_sql=""
        ),
    ]
