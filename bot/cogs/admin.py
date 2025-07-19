"""Admin commands cog for Discord bot."""

import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from services import TaskService, ProjectService, UserService
from utils import init_database

logger = logging.getLogger(__name__)


class AdminCog(commands.Cog):
    """Administrative commands for bot management."""
    
    def __init__(self, bot):
        self.bot = bot
    
    def cog_check(self, ctx):
        """Check if user has admin permissions."""
        return ctx.author.guild_permissions.administrator
    
    @app_commands.command(name="admin-stats", description="View bot statistics")
    @app_commands.default_permissions(administrator=True)
    async def admin_stats(self, interaction: discord.Interaction):
        """View bot statistics."""
        try:
            # Get statistics
            all_projects = await ProjectService.get_all_projects(include_inactive=True)
            active_projects = await ProjectService.get_all_projects(include_inactive=False)
            all_users = await UserService.get_all_users()
            
            # Count tasks by status
            all_tasks = []
            for project in all_projects:
                all_tasks.extend(project.tasks)
            
            task_stats = {
                "total": len(all_tasks),
                "todo": len([t for t in all_tasks if t.status == "todo"]),
                "in_progress": len([t for t in all_tasks if t.status == "in_progress"]),
                "review": len([t for t in all_tasks if t.status == "review"]),
                "done": len([t for t in all_tasks if t.status == "done"]),
                "cancelled": len([t for t in all_tasks if t.status == "cancelled"])
            }
            
            embed = discord.Embed(
                title="📊 Bot Statistics",
                color=0x9b59b6,
                timestamp=interaction.created_at
            )
            
            # Project statistics
            embed.add_field(
                name="📁 Projects",
                value=f"Active: {len(active_projects)}\nTotal: {len(all_projects)}",
                inline=True
            )
            
            # User statistics
            embed.add_field(
                name="👥 Users",
                value=f"Registered: {len(all_users)}",
                inline=True
            )
            
            # Task statistics
            task_text = f"""Total: {task_stats['total']}
To Do: {task_stats['todo']}
In Progress: {task_stats['in_progress']}
Review: {task_stats['review']}
Done: {task_stats['done']}
Cancelled: {task_stats['cancelled']}"""
            
            embed.add_field(
                name="📋 Tasks",
                value=task_text,
                inline=True
            )
            
            # Bot info
            embed.add_field(
                name="🤖 Bot Info",
                value=f"Guilds: {len(self.bot.guilds)}\nLatency: {round(self.bot.latency * 1000)}ms",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            await interaction.response.send_message(
                "❌ Failed to retrieve statistics.",
                ephemeral=True
            )
    
    @app_commands.command(name="admin-cleanup", description="Clean up inactive data")
    @app_commands.default_permissions(administrator=True)
    async def admin_cleanup(self, interaction: discord.Interaction):
        """Clean up inactive data."""
        embed = discord.Embed(
            title="🧹 Data Cleanup",
            description="Data cleanup functionality will be implemented with database cleanup routines.",
            color=0xe67e22
        )
        
        embed.add_field(
            name="Planned Cleanup Tasks",
            value="• Remove old completed tasks\n• Clean up inactive users\n• Archive old projects\n• Optimize database performance",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="admin-backup", description="Create data backup")
    @app_commands.default_permissions(administrator=True)
    async def admin_backup(self, interaction: discord.Interaction):
        """Create data backup."""
        embed = discord.Embed(
            title="💾 Data Backup",
            description="Database backup functionality will be implemented with automated backup routines.",
            color=0x3498db
        )
        
        embed.add_field(
            name="Planned Backup Features",
            value="• Database snapshots\n• Task data export\n• Project configuration backup\n• User data preservation",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_commands(self, ctx):
        """Sync slash commands."""
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Synced {len(synced)} commands.")
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
            await ctx.send("❌ Failed to sync commands.")
    
    @commands.command(name="reload")
    @commands.has_permissions(administrator=True)
    async def reload_cog(self, ctx, cog_name: str):
        """Reload a specific cog."""
        try:
            await self.bot.reload_extension(f"bot.cogs.{cog_name}")
            await ctx.send(f"✅ Reloaded cog: {cog_name}")
            logger.info(f"Reloaded cog: {cog_name}")
        except Exception as e:
            logger.error(f"Failed to reload cog {cog_name}: {e}")
            await ctx.send(f"❌ Failed to reload cog: {cog_name}")
    
    @commands.command(name="db-init")
    @commands.has_permissions(administrator=True)
    async def init_db(self, ctx):
        """Initialize database tables."""
        try:
            await init_database()
            await ctx.send("✅ Database initialized successfully.")
            logger.info("Database initialized via admin command")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            await ctx.send("❌ Failed to initialize database.")


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(AdminCog(bot))