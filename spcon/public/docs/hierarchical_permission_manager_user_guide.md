# Hierarchical Permission Manager - User Guide

## Purpose

Hierarchical Permission Manager is used to control ERPNext document access from one screen instead of creating many User Permission records manually.

Use this when users should see records based on reporting hierarchy, for example CEO, Manager, Group Leader, and Team Member.

## Main DocType

Open:

Permission Profile

## Example Setup

Create a new Permission Profile:

Profile Name: CRM Permission
Company: SP Concare Private Limited
Enabled: Yes

## Hierarchy Levels Example

Add rows in Hierarchy Levels:

| Level Name | Sequence | Role | Parent Level | Users | Access Scope |
| --- | ---: | --- | --- | --- | --- |
| CEO | 1 | CEO Role |  | ceo@example.com | All Records |
| Manager | 2 | Manager Role | CEO | manager@example.com | All Below Hierarchy |
| Group Leader | 3 | Group Leader Role | Manager | leader@example.com | All Below Hierarchy |
| Team Member | 4 | Team Member Role | Group Leader | member1@example.com, member2@example.com | Own Records |

Users field supports multiple User IDs separated by comma, newline, or semicolon.

## DocType Permissions Example

Add rows in DocType Permissions:

| DocType | Enabled | Apply Role Permissions | Company Field | Owner Field |
| --- | --- | --- | --- | --- |
| Lead | Yes | Yes | company | owner |
| Opportunity | Yes | Yes | company | owner |
| Quotation | Yes | Yes | company | owner |
| Sales Order | Yes | Yes | company | owner |
| Customer | Yes | Yes | company | owner |
| Task | Yes | Yes | company | owner |

## Access Scope Meaning

Own Records: User can access records created by them or assigned to them.

Direct Child Team: User can access own records plus records of users in direct child levels.

All Below Hierarchy: User can access own records plus records of all users below their level.

All Records: User can access all records for configured DocTypes and Company.

## Permission Buttons

Validate Hierarchy: Checks duplicate levels, parent level errors, circular hierarchy, disabled users, and duplicate DocTypes.

Preview Access: Select Preview User and see level, parent, users below, allowed DocTypes, and permission flags.

Apply Permissions: Creates or updates Role Permissions and maps users to roles.

Rebuild Permissions: Re-applies all enabled Permission Profiles.

## Important Notes

Administrator and System Manager bypass this custom restriction.

The permission check is server-side. List View, Form View, API, and reports using Frappe permission hooks will follow the hierarchy.

Do not create manual User Permission records for the same requirement unless there is a separate business reason.

After changing hooks or installing this feature, run:

bench --site spcon.sanpra migrate
bench --site spcon.sanpra clear-cache

## Quick Test

1. Create one Lead as member1@example.com.
2. Login as member1@example.com. The user should see only own or assigned Leads.
3. Login as leader@example.com. The user should see their own Leads plus member1/member2 Leads.
4. Login as manager@example.com. The user should see all records below Manager.
5. Login as ceo@example.com. The user should see all configured records.
