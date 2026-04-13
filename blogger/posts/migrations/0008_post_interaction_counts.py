from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_alter_post_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='total_comments',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='post',
            name='total_likes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='post',
            name='total_shares',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunSQL(
            sql="""
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
                    'likes_count', p.total_likes,
                    'comments_count', p.total_comments,
                    'share_count', p.total_shares,
                    'created_at', p.created_at,
                    'updated_at', p.updated_at
                ) INTO result
                FROM posts_post p
                JOIN auth_user u ON u.id = p.author_id
                WHERE p.id = p_post_id AND p.status = 'public';

                RETURN result;
            END;
            $$;
            """,
            reverse_sql=""
        ),
        migrations.RunSQL(
            sql="""
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
                WHERE p.status = 'public'
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
                                p.total_likes AS likes_count,
                                p.total_comments AS comments_count,
                                p.total_shares AS share_count,
                                p.created_at,
                                p.updated_at
                            FROM posts_post p
                            JOIN auth_user u ON u.id = p.author_id
                            WHERE p.status = 'public'
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
        )
    ]
