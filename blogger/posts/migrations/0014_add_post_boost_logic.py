from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0013_add_scheduled_at_and_update_functions"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Update get_post_by_id function to include post_boost
            CREATE OR REPLACE FUNCTION get_post_by_id(p_post_id INT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                v_boost_msg TEXT;
            BEGIN
                -- Calculate boost message
                SELECT 
                    CASE 
                        WHEN p.created_at >= '2026-04-11 00:00:00+00' AND p.created_at + INTERVAL '3 hours' > NOW() THEN
                            (EXTRACT(HOUR FROM (p.created_at + INTERVAL '3 hours' - NOW())))::INT || 'hours ' || 
                            (EXTRACT(MINUTE FROM (p.created_at + INTERVAL '3 hours' - NOW())))::INT || 'mins boost remaining'
                        ELSE NULL
                    END INTO v_boost_msg
                FROM posts_post p
                WHERE p.id = p_post_id;

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
                    'scheduled_at', p.scheduled_at,
                    'post_boost', v_boost_msg
                ) INTO result
                FROM posts_post p
                JOIN auth_user u ON u.id = p.author_id
                WHERE p.id = p_post_id 
                  AND (p.status = 'public' OR (p.status = 'scheduled' AND p.scheduled_at <= NOW()));

                RETURN result;
            END;
            $$;

            -- Update get_posts function to include post_boost
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
                                p.scheduled_at,
                                CASE 
                                    WHEN p.created_at >= '2026-04-11 00:00:00+00' AND p.created_at + INTERVAL '3 hours' > NOW() THEN
                                        (EXTRACT(HOUR FROM (p.created_at + INTERVAL '3 hours' - NOW())))::INT || 'hours ' || 
                                        (EXTRACT(MINUTE FROM (p.created_at + INTERVAL '3 hours' - NOW())))::INT || 'mins boost remaining'
                                    ELSE NULL
                                END AS post_boost
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
