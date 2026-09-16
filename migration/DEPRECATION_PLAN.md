# NYCH Migration / Deprecation Plan

**American Milestone Inc. | Nicholas Hartman | Current synthesis: August 2026**

## 1. Purpose

This document outlines the migration and deprecation plan for superseded NYCH repositories or modules. It ensures that historical code is preserved, documented, and migrated safely to the canonical implementation.

## 2. Pre-Migration Requirements

Before any migration or deprecation:

1. **Lineage documented**: All historical repositories/modules must be documented in `docs/NYCH_LINEAGE.md`.
2. **Authority boundaries established**: The canonical implementation authority must be clearly identified.
3. **Schema mismatches identified**: All schema differences between old and new must be cataloged.
4. **Test plan created**: Tests must prove preserved behavior before and after migration.
5. **Rollback plan defined**: Each migration step must be reversible.

## 3. Migration Strategy

### 3.1 Small Reversible Change Groups

Implement changes in small, reversible groups:

1. **Group 1**: Typed interfaces (NychPacket, NychContext, NychState)
   - Add typed interfaces to canonical repo
   - Add adapters in old repos to use new interfaces
   - Run tests to verify behavior preserved

2. **Group 2**: Pipeline stages
   - Implement each stage in canonical repo
   - Add compatibility adapters in old repos
   - Run end-to-end tests

3. **Group 3**: Schema validators
   - Implement QSON, GST, G8SON, MG8 validators
   - Add validation at repository boundaries
   - Run conformance tests

4. **Group 4**: Evidence emission
   - Implement evidence emission in canonical format
   - Migrate old evidence formats to canonical
   - Validate emitted artifacts

### 3.2 Dependency Management

- Old repos should depend on canonical interfaces, not duplicate them.
- Use explicit versioning for all dependencies.
- Maintain backward compatibility during transition period.

## 4. Deprecation Criteria

A module/repository may be deprecated when:

1. All functionality is available in the canonical implementation
2. All tests pass against the canonical implementation
3. No active users remain on the old implementation
4. Documentation clearly points to the canonical replacement
5. A deprecation notice has been in place for at least one release cycle

## 5. Deprecation Process

1. **Announce deprecation**: Add deprecation notice to README and code comments
2. **Provide migration guide**: Document how to migrate to canonical implementation
3. **Maintain compatibility**: Keep old code functional but mark as deprecated
4. **Monitor usage**: Track any remaining usage of deprecated code
5. **Remove after grace period**: Remove deprecated code after agreed grace period

## 6. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking changes to interfaces | Medium | High | Version interfaces; maintain backward compatibility |
| Data loss during migration | Low | High | Backup all data before migration; test restore |
| Performance regression | Low | Medium | Benchmark before and after; optimize if needed |
| User confusion | Medium | Low | Clear documentation; migration guides |
| Rollback failure | Low | High | Test rollback procedures; maintain backups |

## 7. Rollback Plan

Each migration step must have a rollback plan:

1. **Before migration**: Create backup of current state
2. **During migration**: Run tests after each step
3. **If failure**: Restore from backup; document failure cause
4. **After rollback**: Analyze failure; adjust migration plan

## 8. Communication Plan

- **Before migration**: Announce planned changes to all stakeholders
- **During migration**: Provide regular status updates
- **After migration**: Document completion; update documentation
- **Ongoing**: Monitor for issues; provide support for migration questions

## 9. Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| Assessment | 1 week | Inventory, classification, risk assessment |
| Planning | 1 week | Migration plan, test plan, rollback plan |
| Implementation | 2-4 weeks | Implement canonical code, adapters, tests |
| Migration | 1-2 weeks | Migrate users, monitor, support |
| Deprecation | 2-4 weeks | Announce deprecation, maintain compatibility |
| Removal | 1 week | Remove deprecated code after grace period |

## 10. Success Criteria

Migration is successful when:

1. All functionality is available in canonical implementation
2. All tests pass
3. No active users remain on deprecated code
4. Documentation is complete and accurate
5. Performance is equal or better than before
